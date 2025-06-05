import uuid
from typing import Optional

from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy.orm import Session

from csotanypoker.models.player import Player
from csotanypoker.models.room import Room
from csotanypoker.models.user import User
from csotanypoker.server.database import (
    Base,
    DBCard,
    DBPlayer,
    DBRoom,
    DBUser,
    Game,
    engine,
    get_db_session,
)
from csotanypoker.server.game_background import GameLogic

app = Flask(__name__)
app.secret_key = "titkos_kulcs"  # Secret key needed for session handling
socketio = SocketIO(app, cors_allowed_origins="*")


sockets = {}

ROOMS = []
USERS = []


game_instances = {}


def reset_database():  # this is only needed for testing
    Base.metadata.drop_all(bind=engine)  # deletes all tables
    Base.metadata.create_all(bind=engine)


@socketio.on("connect")
def handle_connect() -> None:
    print("Kliens csatlakozott")


@socketio.on("register")
def handle_register(data: dict) -> None:
    db: Session = get_db_session()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        emit("register_error", {"message": "Felhasználónév és jelszó nem lehet üres."})
        db.close()
        return

    existing_user = db.query(DBUser).filter(DBUser.username == username).first()
    if existing_user:
        emit("register_error", {"message": "Ez a felhasználónév már foglalt."})
        db.close()
        return

    new_user = DBUser(username=username, password=password, is_active=False)
    db.add(new_user)
    db.commit()
    db.close()

    handle_login({"username": username, "password": password})


@socketio.on("rejoin_waiting_room")
def handle_start_new_game(data: dict):
    username = data["username"]
    db: Session = get_db_session()
    username = session.get("username")

    db_user: Optional[DBUser] = (
        db.query(DBUser).filter(DBUser.username == username).first()
    )

    room_id = db_user.current_room_id

    target_room = None
    for room in ROOMS:
        if room.room_id == room_id:
            target_room = room
            break
    for user in USERS:
        if user.username == username:
            if user not in target_room.users:
                target_room.users.append(user)
            user.current_room_id = room_id
            break

    reset_room_state(room_id)
    socketio.emit(
        "rejoin_waiting_success",
        {
            "room_id": room_id,
            "players": [u.username for u in target_room.users],
            "activ_users": [u.username for u in USERS if u.is_active],
            "max_player_count": target_room.max_player_count,
        },
        to=request.sid,
    )

    if len(target_room.users) >= target_room.max_player_count:
        player_usernames = [user.username for user in target_room.users]
        target_room.game_started = True
        socketio.emit("start_game", {"players": player_usernames}, room=room_id)
        start_game(player_usernames, room_id)

    broadcast_room_list_update()


def reset_room_state(room_id: str) -> str:
    db: Session = get_db_session()
    game = db.query(Game).filter_by(room_id=room_id).first()
    if game:
        db.delete(game)
    players = (
        db.query(DBPlayer).join(DBUser).filter(DBUser.current_room_id == room_id).all()
    )
    for player in players:
        db.delete(player)

    db_room = db.query(DBRoom).filter_by(room_id=room_id).first()

    if db_room:
        db_room.set_game_started(False)

    db.commit()
    db.close()

    for room in ROOMS:
        if room.room_id == room_id:
            room.game_started = False
            break


@socketio.on("login")
def handle_login(data: dict) -> None:
    db: Session = get_db_session()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        emit("login_error", {"message": "Felhasználónév és jelszó nem lehet üres."})
        db.close()
        return

    dbuser: Optional[DBUser] = (
        db.query(DBUser).filter(DBUser.username == username).first()
    )

    if not dbuser or dbuser.password != password:
        emit("login_error", {"message": "Hibás felhasználónév vagy jelszó."})
        db.close()
        return

    if dbuser.is_active:
        emit("login_error", {"message": "Ez a felhasználó már be van jelentkezve."})
        db.close()
        return

    session["socket_id"] = request.sid
    sockets[username] = session["socket_id"]
    session["username"] = username

    previous_room_id = dbuser.current_room_id
    previous_room = None

    if previous_room_id:
        for room in ROOMS:
            if room.room_id == previous_room_id:
                previous_room = room
                break

    for user in USERS:
        if user.username == username:
            user.is_active = True
            break
    dbuser.set_active(True)
    db.commit()

    rooms_data = get_rooms_data()
    emit("login_success", {"username": username, "rooms": rooms_data})

    existing_user = next((user for user in USERS if user.username == username), None)
    if not existing_user:
        USERS.append(User(username=username, is_active=True, current_room_id=None))
    else:
        existing_user.is_active = True
        existing_user.current_room_id = None
    if previous_room:
        user_in_room = any(user.username == username for user in previous_room.users)
        if user_in_room:
            emit(
                "reconnect_offer",
                {
                    "username": username,
                    "rooms": rooms_data,
                    "previous_room_id": previous_room.room_id,
                },
            )
            db.close()
            return
        else:
            dbuser.current_room_id = None
            db.commit()

    db.close()


def get_rooms_data():
    rooms_data = {}
    for room in ROOMS:
        if not room.game_started:
            rooms_data[room.room_id] = {
                "name": room.name,
                "player_count": room.max_player_count,
                "password_protected": True if room.password else False,
                "actual_player_count": len([user for user in room.users if user]),
            }
    return rooms_data


def broadcast_room_list_update():
    rooms_data = get_rooms_data()
    for user in USERS:
        if user.username in sockets and not user.current_room_id:
            socketio.emit(
                "rooms_updated", {"rooms": rooms_data}, to=sockets[user.username]
            )


@socketio.on("disconnect")
def handle_disconnect() -> None:
    print("Kliens lecsatlakozott")
    username = session.get("username")
    if not username:
        return

    user = next((u for u in USERS if u.username == username), None)
    if user:
        user.is_active = False

    db: Session = get_db_session()
    dbuser: Optional[DBUser] = db.query(DBUser).filter_by(username=username).first()
    if dbuser:
        dbuser.set_active(False)
        db.commit()
    db.close()

    sockets.pop(username, None)

    if user and user.current_room_id:
        room = next((r for r in ROOMS if r.room_id == user.current_room_id), None)
        if room:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in room.users],
                    "activ_users": [u.username for u in USERS if u.is_active],
                    "max_player_count": room.max_player_count,
                },
                room=user.current_room_id,
            )


@socketio.on("leave_room")
def handle_leave_room(data: dict) -> None:
    """
    Handle user leaving a room
    """
    db: Session = get_db_session()
    username = session.get("username")

    db_user: Optional[DBUser] = (
        db.query(DBUser).filter(DBUser.username == username).first()
    )

    room_id = db_user.current_room_id

    target_room = None
    for room in ROOMS:
        if room.room_id == room_id:
            target_room = room
            break

    user_to_remove = None
    for user in USERS:
        if user.username == username:
            user_to_remove = user
            break

    if user_to_remove and user_to_remove in target_room.users:
        target_room.users.remove(user_to_remove)
        user_to_remove.current_room_id = None

        db_user.current_room_id = None
        db.commit()
        leave_room(room_id)
        emit("left_room", {"message": "Szoba elhagás"})

        if target_room.users:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in target_room.users],
                    "activ_users": [u.username for u in USERS if u.is_active],
                    "max_player_count": target_room.max_player_count,
                },
                room=room_id,
            )
        else:
            ROOMS.remove(target_room)

    broadcast_room_list_update()

    db.close()


@socketio.on("create_room")
def create_room(data: dict) -> None:
    db: Session = get_db_session()
    username = session.get("username")

    room_id: str = str(uuid.uuid4())
    dbroom = DBRoom(
        room_id=room_id, name=data["room_name"], player_count=data["max_player_count"]
    )

    password = None
    if data["password_protected"]:
        password = data["password"]
        dbroom.password = password

    room = Room(
        room_id=room_id,
        name=data["room_name"],
        max_player_count=data["max_player_count"],
    )
    room.password = password

    db.add(dbroom)
    db.commit()

    ROOMS.append(room)
    join_user_to_room(room_id, username, skip_password_check=True)

    broadcast_room_list_update()


@socketio.on("join_room")
def join_room_request(data: dict) -> None:
    username = session.get("username")
    room_id = data["room_id"]
    provided_password = data.get("password", "")
    skipp_password_check = data["skipp_password"]

    if skipp_password_check or validate_room_password(room_id, provided_password):
        join_user_to_room(room_id, username)
    else:
        emit("join_room_error", {"message": "Helytelen jelszó"}, to=request.sid)


def validate_room_password(room_id: str, provided_password: str) -> bool:
    db: Session = get_db_session()
    room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

    if not room:
        return False

    if not room.password:
        return True

    return room.password == provided_password


def join_user_to_room(
    room_id: str, username: str, skip_password_check: bool = False
) -> None:
    db: Session = get_db_session()
    db_user: Optional[DBUser] = (
        db.query(DBUser).filter(DBUser.username == username).first()
    )
    target_room = None
    for room in ROOMS:
        if room.room_id == room_id:
            target_room = room
            break

    for user in USERS:
        if user.username == username:
            if user not in target_room.users:
                target_room.users.append(user)
            user.current_room_id = room_id
            break

    join_room(room_id)
    db_user.current_room_id = room_id
    db.commit()
    room_joined()
    broadcast_room_list_update()

    socketio.emit(
        "room_players_updated",
        {
            "room_id": room_id,
            "players": [u.username for u in target_room.users],
            "activ_users": [u.username for u in USERS if u.is_active],
            "max_player_count": target_room.max_player_count,
        },
        room=room_id,
    )

    if len(target_room.users) >= target_room.max_player_count:
        player_usernames = [user.username for user in target_room.users]
        target_room.game_started = True
        socketio.emit("start_game", {"players": player_usernames}, room=room_id)
        start_game(player_usernames, room_id)

        broadcast_room_list_update()


def room_joined() -> None:
    db: Session = get_db_session()
    username = session.get("username")
    user: Optional[DBUser] = (
        db.query(DBUser).filter(DBUser.username == username).first()
    )
    current_room = None
    for room in ROOMS:
        if room.room_id == user.current_room_id:
            current_room = room
            break

    player_names = [u.username for u in current_room.users]

    emit(
        "joined_room",
        {
            "room_id": current_room.room_id,
            "password": current_room.password if current_room.password else None,
            "name": current_room.name,
            "players": player_names,
            "username": username,
            "max_player_count": current_room.max_player_count,
        },
        to=request.sid,
    )


def get_user_room_id(username: str) -> Optional[str]:
    db: Session = get_db_session()
    user: Optional[DBUser] = (
        db.query(DBUser).filter(DBUser.username == username).first()
    )
    db.close()
    return user.current_room_id if user else None


def get_game_instance(room_id: str) -> Optional[GameLogic]:
    return game_instances.get(room_id)


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid
    username = session.get("username")
    room_id = get_user_room_id(username)
    room: DBRoom = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

    game = db.query(Game).filter(Game.room_id == room.room_id).first()
    game_instance = get_game_instance(room_id)

    for card in game_instance.state.deck:
        if card.name == data["selected_card"]:
            game_instance.state.question_card = card
            break

    game_instance.select_target_player(data["selected_player"])
    game_instance.make_statement(statement=data["set_card_giver"])

    if not data["pass"]:
        if game_instance.has_cards_in_hand():
            game_end(room_id)
            db.close()
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
    socketio.emit(
        "card_passing",
        {
            "player_statement": data["set_card_giver"],
            "card_giver": game_instance.state.active_player.name,
            "targeted_player": game_instance.state.targeted_player.name,
            "visited_by": game_instance.state.question_card.visited_already,
        },
        room=room_id,
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
    db.close()


def card_content(room_id: str):
    db: Session = get_db_session()
    game_instance = get_game_instance(room_id)

    if game_instance:
        socketio.emit(
            "card_content",
            {
                "card_type": game_instance.state.question_card.type,
                "card_index": game_instance.state.question_card.index,
                "visited_by": game_instance.state.question_card.visited_already,
            },
            room=room_id,
        )
    db.close()


@socketio.on("guess")
def handle_guess(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)

    game_instance = get_game_instance(room_id)

    guess = data["guess"]
    result = game_instance.check_truth(guess)
    card_content(room_id)
    if result:
        game_instance.place_card(game_instance.state.active_player)
    else:
        game_instance.place_card(game_instance.state.targeted_player)

    place_card(room_id)


@socketio.on("pass")
def handle_pass(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid
    username = session.get("username")
    room_id = get_user_room_id(username)
    game_instance = get_game_instance(room_id)

    if game_instance.state.targeted_player is not None:
        game_instance.state.active_player = game_instance.state.targeted_player
        game_instance.state.targeted_player = None

        socketio.emit(
            "passed",
            {
                "message": f"{game_instance.state.active_player.name} passed!",
                "active_player": game_instance.state.active_player.name,
            },
            room=room_id,
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

    db.close()


def place_card(room_id: str) -> None:
    db = get_db_session()
    game_instance = get_game_instance(room_id)

    if not game_instance:
        db.close()
        return

    player_data = {}
    for j in game_instance.state.players:
        print(j.cards_in_front)
        player_data[j.name] = {
            "cards_in_front": j.cards_in_front,
            "card_count": len(j.cards_in_hand),
        }

    socketio.emit(
        "card_placed",
        {
            "player": game_instance.state.active_player.name,
            "card_type": game_instance.state.question_card.type
            if game_instance.state.question_card
            else "ismeretlen",
            "active_player": game_instance.state.active_player.name,
        },
        room=room_id,
    )

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
        game_end(room_id)

    db.close()


def game_end(room_id: str) -> None:
    db = get_db_session()
    room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
    game = db.query(Game).filter(Game.room_id == room.room_id).first()
    game_instance = get_game_instance(room_id)

    if game and game_instance:
        game.loser = game_instance.state.active_player.name
        db.commit()

        socketio.emit(
            "game_over",
            {
                "losing_player": game_instance.state.active_player.name,
            },
            room=room_id,
        )

        if room_id in game_instances:
            del game_instances[room_id]

    db.close()


def start_game(players: list, room_id: str) -> None:
    """
    Start the game with the given players in the specified room.

    Args:
        players (list): List of player usernames.
        room_id (str): Room identifier where the game should start.
    """
    global game_instances
    db = get_db_session()
    players_to_delete = (
        db.query(DBPlayer).join(DBUser).filter(DBUser.current_room_id == room_id).all()
    )
    for p in players_to_delete:
        db.delete(p)
    db.commit()
    game_instances[room_id] = GameLogic([Player(str(user)) for user in players])
    game_instance = game_instances[room_id]

    db = get_db_session()

    game = Game(room_id=room_id)
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
    db.close()


if __name__ == "__main__":
    reset_database()
    socketio.run(app, debug=True, host="0.0.0.0")
