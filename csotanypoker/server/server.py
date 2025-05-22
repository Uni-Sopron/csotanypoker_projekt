import uuid
from typing import Optional

from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy.orm import Session

from csotanypoker.models.model import Player
from csotanypoker.server.adatbazis import (Base, DBCard, DBPlayer, Game, Room,
                                           User, engine, get_db_session)
from csotanypoker.server.jatek_hatter import GameLogic

app = Flask(__name__)
app.secret_key = "titkos_kulcs"  # Secret key needed for session handling
socketio = SocketIO(app, cors_allowed_origins="*")


sockets = {}


def reset_database():  # this is only needed for testing
    Base.metadata.drop_all(bind=engine)  # deletes all tables
    Base.metadata.create_all(bind=engine)


@socketio.on("connect")
def handle_connect() -> None:
    print("Kliens csatlakozott")


game_instance = None  # Initialize the game instance


@socketio.on("login")
def handle_login(data: dict) -> None:
    """
    Login event handler.

    This function checks whether the username already exists,
    and if so, verifies if the user is active.

    Args:
        data (dict): Dictionary containing the username.
    """
    db: Session = get_db_session()
    user: Optional[User] = (
        db.query(User).filter(User.username == data["username"]).first()
    )
    username: str = data["username"]

    if user and user.is_active:
        emit(
            "login_error",
            {"message": "Ez a felhasználónév már foglalt."},
        )

        db.close()
        return

    session["socket_id"] = request.sid
    sockets[username] = session["socket_id"]
    session["username"] = username
    if not user:
        db.add(User(username=username, is_active=True))
    else:
        user.set_active(True)

    room = db.query(Room).filter(Room.name == "game").first()
    if not room:
        # If such room doesn't exist yet, we create it
        room_id: str = str(uuid.uuid4())
        room = Room(room_id=room_id, name="game")
        db.add(room)
        db.commit()

    user = db.query(User).filter(User.username == username).first()

    user.current_room_id = room.room_id
    db.commit()

    join_room(room.room_id)

    # Query players
    player_names: list = [user.username for user in room.users if user.is_active]
    print("nevek", player_names)
    emit("login_success", {"username": username, "screen_state": "waiting"})
    emit(
        "player_joined",
        {
            "players": player_names,
            "joined_player": username,
        },
        room=room.room_id,
    )

    emit(
        "joined_room",
        {
            "room_id": room.room_id,
            "name": room.name,
            "players": player_names,
            "username": username,
        },
    )

    # If there are enough players, the game can be started
    if len(player_names) >= room.player_count:
        room.game_started = True
        db.commit()
        emit("start_game", {"players": player_names}, room=room.room_id)
        print("Játék elindult")
        start_game(player_names)

    db.close()


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid
    room = db.query(Room).filter(Room.name == "game").first()
    game = db.query(Game).filter(Game.room_id == room.room_id).first()
    for card in game_instance.state.deck:
        if card.name == data["selected_card"]:
            game_instance.state.question_card = card
            break

    game_instance.select_target_player(data["selected_player"])
    game_instance.make_statement(statement=data["set_card_giver"])

    if not data["pass"]:
        if game_instance.has_cards_in_hand():
            game_end()
            return
        game_instance.select_card(
            selected_card_id=game_instance.state.question_card.name
        )
        player_db = (
            db.query(DBPlayer)
            .filter(DBPlayer.name == game_instance.state.active_player.name)
            .first()
        )
        card_db = (
            db.query(DBCard)
            .filter(DBCard.name == game_instance.state.question_card.name)
            .first()
        )

        if player_db and card_db and card_db in player_db.hand_cards:
            player_db.hand_cards.remove(card_db)
            db.commit()
        cards_in_hand = [
            k.name for k in game_instance.state.active_player.cards_in_hand
        ]
        print("jatekos_neve", game_instance.state.active_player.name)
        print("cards_in_hand", cards_in_hand)
        emit(
            "cards_in_hand",
            {
                "cards_in_hand": cards_in_hand,
            },
            to=sid,
        )

    if (
        game_instance.state.targeted_player.name
        not in game_instance.state.question_card.visited_already
    ):
        game_instance.state.question_card.visited_already.append(
            game_instance.state.targeted_player.name
        )
        player_db = (
            db.query(DBPlayer)
            .filter(DBPlayer.name == game_instance.state.targeted_player.name)
            .first()
        )
        card_db = (
            db.query(DBCard)
            .filter(DBCard.name == game_instance.state.question_card.name)
            .first()
        )
        card_db.previous_holders.append(player_db)
    emit(
        "card_passing",
        {
            "player_statement": data["set_card_giver"],
            "card_giver": game_instance.state.active_player.name,
            "targeted_player": game_instance.state.targeted_player.name,
            "visited_by": game_instance.state.question_card.visited_already,
        },
        room=room.room_id,
    )

    for j in game_instance.state.players:
        player_sid = sockets[j.name]
        if (
            player_sid
            and j.name in game_instance.state.question_card.visited_already
            and j.name != game_instance.state.targeted_player.name
        ):
            emit(
                "card_content",
                {
                    "card_type": game_instance.state.question_card.type,
                    "card_index": game_instance.state.question_card.index,
                    "visited_by": game_instance.state.question_card.visited_already,
                },
                to=player_sid,
            )

    game.active_player_name = (
        game_instance.state.active_player.name
        if game_instance.state.active_player
        else None
    )
    game.target_player_name = (
        game_instance.state.targeted_player.name
        if game_instance.state.targeted_player
        else None
    )
    game.questioned_card_name = (
        game_instance.state.question_card.name
        if game_instance.state.question_card
        else None
    )
    db.commit()


def card_content():
    db: Session = get_db_session()
    room = db.query(Room).filter(Room.name == "game").first()
    emit(
        "card_content",
        {
            "card_type": game_instance.state.question_card.type,
            "card_index": game_instance.state.question_card.index,
            "visited_by": game_instance.state.question_card.visited_already,
        },
        room=room.room_id,
    )


@socketio.on("guess")
def handle_guess(data: dict) -> None:
    guess = data["guess"]
    result = game_instance.check_truth(guess)
    card_content()
    if result:
        game_instance.place_card(game_instance.state.active_player)
    else:
        game_instance.place_card(game_instance.state.targeted_player)

    place_card()


@socketio.on("pass")
def handle_pass(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid

    room: Room = db.query(Room).filter(Room.name == "game").first()

    # Check that the target player is not None
    if game_instance.state.targeted_player is not None:
        game_instance.state.active_player = game_instance.state.targeted_player
        game_instance.state.targeted_player = None

        emit(
            "passed",
            {
                "message": f"{game_instance.state.active_player.name} passed!",
                "active_player": game_instance.state.active_player.name,
            },
            room=room.room_id,
        )

        emit(
            "card_content",
            {
                "card_type": game_instance.state.question_card.type,
                "card_index": game_instance.state.question_card.index,
                "visited_by": game_instance.state.question_card.visited_already,
            },
            to=sid,
        )
        print(
            "game_instance.state.kerdeses_kartya",
            game_instance.state.question_card.name,
        )


def place_card() -> None:
    db = get_db_session()
    room = db.query(Room).filter(Room.name == "game").first()
    player_data = {}
    for j in game_instance.state.players:
        print(j.cards_in_front)
        player_data[j.name] = {
            "cards_in_front": j.cards_in_front,
            "card_count": len(j.cards_in_hand),
        }

    # Send broadcast about the placed card
    emit(
        "card_placed",
        {
            "player": game_instance.state.active_player.name,
            "card_type": game_instance.state.question_card.type
            if game_instance.state.question_card
            else "ismeretlen",
            "active_player": game_instance.state.active_player.name,
        },
        room=room.room_id,
    )

    # Reset the questioned card
    game_instance.state.question_card = None

    for j in game_instance.state.players:
        player_sid = sockets[j.name]
        if player_sid:
            cards_in_hand = [k.name for k in j.cards_in_hand]
            emit(
                "player_data",
                {
                    "name": j.name,
                    "cards_in_hand": cards_in_hand,
                    "starting_player": game_instance.state.active_player.name,
                    "player_data": player_data,
                },
                to=player_sid,
            )

    if game_instance.has_4_cards_in_front():
        game_end()


def game_end() -> None:
    db = get_db_session()
    room = db.query(Room).filter(Room.name == "game").first()
    game = db.query(Game).filter(Game.room_id == room.room_id).first()
    game.winner = game_instance.state.active_player.name
    db.commit()
    emit(
        "game_over",
        {
            "losing_player": game_instance.state.active_player.name,
        },
        room=room.room_id,
    )


def start_game(players: list) -> None:
    """
    Start the game with the given players.

    Args:
        players (list): List of player usernames.
    """
    global game_instance
    print("players", players)
    game_instance = GameLogic([Player(str(user)) for user in players])

    db = get_db_session()
    username = session.get("username")
    user: Optional[User] = db.query(User).filter(User.username == username).first()

    game = Game(room_id=user.current_room_id)
    db.add(game)
    db.commit()

    for card in game_instance.state.deck:
        existing_card = db.query(DBCard).filter_by(name=card.name).first()

        if not existing_card:
            card_db = DBCard(name=card.name)
            db.add(card_db)

    for j in game_instance.state.players:
        player = DBPlayer(name=j.name, statement=j.statement)
        db.add(player)

        for card in j.cards_in_hand:
            card_db = db.query(DBCard).filter_by(name=card.name).first()
            if card_db:
                player.hand_cards.append(card_db)

    db.commit()

    active_name = game_instance.state.active_player.name

    player_data = {}
    for j in game_instance.state.players:
        print(j.cards_in_front)
        player_data[j.name] = {
            "cards_in_front": j.cards_in_front,
            "card_count": len(j.cards_in_hand),
        }
        print("kartyak szama", len(j.cards_in_hand))

    for j in game_instance.state.players:
        player_sid = sockets[j.name]
        if player_sid:
            cards_in_hand = [k.name for k in j.cards_in_hand]
            emit(
                "player_data",
                {
                    "name": j.name,
                    "cards_in_hand": cards_in_hand,
                    "starting_player": active_name,
                    "player_data": player_data,
                },
                to=player_sid,
            )
        print("cards_in_hand", cards_in_hand)


if __name__ == "__main__":
    reset_database()
    socketio.run(app, debug=True, host="0.0.0.0")
