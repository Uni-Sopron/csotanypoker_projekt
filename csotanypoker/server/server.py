from typing import Optional
import random
from typing import Set
from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy.orm import Session, sessionmaker
from csotanypoker.models.animal import Animal
from dotenv import load_dotenv  
import os
from csotanypoker.models.user import Client_User, AI_NAMES
from csotanypoker.server.database import (
    engine,
    DBUser,
    DBRoom,
    DBGame,
    create_tables,
)
from csotanypoker.server.room_manager import RoomManager
from csotanypoker.server.game_manager import GameManager

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY", "titkos_kulcs")
socketio = SocketIO(app, cors_allowed_origins="*")

sockets = {}
game_instances = {}


room_manager = RoomManager(socketio, sockets)
game_manager = GameManager(socketio, sockets, room_manager)


def weighted_random_choice(choices_weights):
    if not choices_weights:
        return None

    import random

    choices = list(choices_weights.keys())
    weights = list(choices_weights.values())
    weights = [max(0.1, w) for w in weights]
    return random.choices(choices, weights=weights)[0]


def get_db_session():
    Session = sessionmaker(bind=engine)
    return Session()


def get_user_by_username(username: str) -> Optional[DBUser]:
    with get_db_session() as db:
        return db.query(DBUser).filter(DBUser.username == username).first()


def all_players_active_in_room(room_id: str) -> bool:
    with get_db_session() as db:
        return room_manager.all_players_active_in_room(db, room_id)


def get_rooms_data():
    with get_db_session() as db:
        return room_manager.get_rooms_data(db)


def validate_room_password(room_id: str, provided_password: str) -> bool:
    with get_db_session() as db:
        return room_manager.validate_room_password(db, room_id, provided_password)


def remove_all_users_from_room(room_id: str, reconnecting: bool = False) -> None:
    with get_db_session() as db:
        current_username = session.get("username")
        room_manager.remove_all_users_from_room(
            db, room_id, current_username, reconnecting
        )


@socketio.on("connect")
def handle_connect() -> None:
    print("Kliens csatlakozott")


@socketio.on("register")
def handle_register(data: dict) -> None:
    db: Session = get_db_session()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    existing_user = db.query(DBUser).filter(DBUser.username == username).first()
    if existing_user:
        emit("register_error", {"message": "Ez a felhasználónév már foglalt."})
        db.close()
        return

    new_db_user = DBUser(username=username, password=password, is_active=False)
    db.add(new_db_user)
    db.commit()
    db.close()

    handle_login({"username": username, "password": password})


@socketio.on("rejoin_game")
def handle_rejoin_game() -> None:
    username = session.get("username")
    if not username:
        print("Nincs bejelentkezett felhasználó a session-ben")
        return
    if username not in sockets:
        print(f"Nincs aktív socket kapcsolat {username} felhasználóhoz")
        return

    with get_db_session() as db:
        db_user: Optional[DBUser] = (
            db.query(DBUser).filter(DBUser.username == username).first()
        )
        db_user.is_active = True
        db.commit()

        if not db_user or not db_user.current_room_id:
            print(f"Felhasználó nem aktív vagy nincs szobája: {username}")
            return

        room_id = db_user.current_room_id
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if not target_room:
            print(f"Szoba nem található: {room_id}")
            return

        sockets[username] = request.sid

        if db_user.current_room_id != room_id:
            db_user.current_room_id = room_id
            db.commit()

        join_room(room_id)
        room_manager.update_room_player_count(room_id)

        print(f"szoba id: {room_id}, szoba neve: {target_room.name}")

        room_users = room_manager.get_room_users(room_id)

        if len(room_users) >= target_room.max_player_count:
            player_usernames = [user.username for user in room_users]

            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )
            print("rejoin_waiting_room: Játék indul a szobában:", room_id)
            game_manager.start_game(db, player_usernames, room_id, reconnect=True)

        game_manager.resume_ai_activity_if_needed(db, room_id)


@socketio.on("rejoin_waiting_room")
def handle_start_new_game(data: dict):
    username = session.get("username")
    if not username:
        return
    if username not in sockets:
        return

    with get_db_session() as db:
        db_user: Optional[DBUser] = (
            db.query(DBUser).filter(DBUser.username == username).first()
        )
        db_user.is_active = True
        db.commit()
        if not db_user or not db_user.current_room_id:
            print(f"Felhasználó nem aktív vagy nincs szobája: {username}")
            return

        room_id = db_user.current_room_id
        target_room = room_manager.get_room_by_id(db, room_id)
        target_game = (
            db.query(DBGame)
            .filter(DBGame.room_id == room_id, DBGame.game_status == "run")
            .first()
        )
        if not target_room:
            print(f"Szoba nem található: {room_id}")
            return

        sockets[username] = request.sid

        if db_user.current_room_id != room_id:
            db_user.current_room_id = room_id
            db.commit()

        join_room(room_id)
        room_manager.update_room_player_count(db, room_id)

        print(f"szoba id: {room_id}, szoba neve: {target_room.name}")

        users = room_manager.get_client_users_in_room(db, room_id)

        socketio.emit(
            "rejoin_waiting_success",
            {
                "room_id": room_id,
                "room_name": target_room.name,
                "players": [u.model_dump() for u in users],
                "max_player_count": target_room.max_player_count,
            },
            to=request.sid,
        )

        socketio.emit(
            "player_rejoined",
            {
                "rejoined_player": username,
            },
            room=room_id,
        )

        room_users = room_manager.get_room_users(db, room_id)
        player_usernames = [user.username for user in room_users]

        print("JATEKOSSZAM", len(room_users))
        if len(room_users) >= target_room.max_player_count:
            if target_game:
                game_instance = game_manager.get_game_instance(room_id)
                if game_instance:
                    game_manager.send_game_state_to_players(
                        db, game_instance, room_id, hide_card_for_unvisited=True
                    )
                    game_manager.resume_ai_activity_if_needed(db, room_id)
                    return

            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )

            print("rejoin_waiting_room: Játék indul a szobában:", room_id)
            game_manager.start_game(db, player_usernames, room_id)

        room_manager.broadcast_room_list_update(db)


@socketio.on("all_players_leave_room")
def handle_all_players_leave_room(data) -> None:
    room_id = data["room_id"]
    remove_all_users_from_room(room_id, data.get("reconnecting", False))


@socketio.on("vote_rematch")
def handle_vote_rematch(data: dict) -> None:
    print("Szavazás a visszavágóra:", data)
    room_id = data["room_id"]
    username = data["username"]

    with get_db_session() as db:
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not target_room:
            return

        print(f"Szobánév: {target_room.name}")

        game_instance = game_manager.get_game_instance(room_id)
        if game_instance:
            game_instance.state.voters.add(username)

        room_users = room_manager.get_room_users(db, room_id)
        if (
            len(game_instance.state.voters)
            + sum(
                1
                for player in game_instance.state.players
                if game_manager.is_ai_player(player.username)
            )
            == target_room.max_player_count
        ):
            players = []
            for user in room_users:
                players.append({"username": user.username, "is_active": user.is_active})

            socketio.emit(
                "start_game",
                {"players": [player["username"] for player in players]},
                room=room_id,
            )

            game_instance.state.voters.clear()

            if room_id in game_instances:
                del game_instances[room_id]

            for game in target_room.games:
                if game.game_status == "run":
                    game.game_status = "end"
            db.commit()

            game_manager.start_game(db, players, room_id)
        else:
            socketio.emit(
                "rematch_vote_received",
                {"voters": list(game_instance.state.voters)},
                room=room_id,
            )


@socketio.on("login")
def handle_login(data: dict) -> None:
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    with get_db_session() as db:
        if not username or not password:
            emit(
                "login_error",
                {"message": "Felhasználónév és jelszó nem lehet üres."},
            )
            return

        dbuser: Optional[DBUser] = (
            db.query(DBUser).filter(DBUser.username == username).first()
        )

        if not dbuser:
            emit("login_error", {"message": "Nem létezik a megadott felhasználónév"})
            return

        if dbuser.password != password:
            emit("login_error", {"message": "Hibás jelszó."})
            return

        if dbuser.is_active:
            emit(
                "login_error",
                {"message": "Ez a felhasználó már be van jelentkezve."},
            )
            return

        dbuser.is_active = True
        db.commit()

        if username in sockets:
            sockets.pop(username, None)
        session["socket_id"] = request.sid
        session["username"] = username
        sockets[username] = request.sid

        previous_room_id = dbuser.current_room_id
        previous_room = (
            db.query(DBRoom).filter(DBRoom.room_id == previous_room_id).first()
            if previous_room_id
            else None
        )

        rooms_data = get_rooms_data()
        user = Client_User(username=username, is_active=True)

        if previous_room and previous_room_id:
            dbuser.is_active = False
            db.commit()
            previous_room_data = {}
            all_rooms = db.query(DBRoom).all()
            for room in all_rooms:
                if room.room_id == previous_room_id:
                    room_player_count = user_counter(room.room_id)
                    previous_room_data = {
                        "room_id": room.room_id,
                        "name": room.name,
                        "player_count": room.max_player_count,
                        "password_protected": True if room.password else False,
                        "actual_player_count": room_player_count,
                    }

            emit(
                "reconnect_offer",
                {
                    "username": username,
                    "rooms": rooms_data,
                    "previous_room": previous_room_data,
                    "game_start": game_is_start(previous_room_id),
                },
                to=sockets[username],
            )

            return
        else:
            emit("login_success", {"user": user.model_dump(), "rooms": rooms_data})


def user_counter(room_id) -> int:
    with get_db_session() as db:
        users = db.query(DBUser).filter(DBUser.current_room_id == room_id).all()
        return len(users)


def game_is_start(room_id: int) -> bool:
    with get_db_session() as db:
        running_game = (
            db.query(DBGame)
            .filter(DBGame.room_id == room_id, DBGame.game_status == "run")
            .first()
        )
        return running_game is not None


@socketio.on("logout")
def handle_logout(data) -> None:
    username = data.get("username")
    if not username:
        username = session.get("username")

    if not username:
        return

    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if db_user and this_is_ai_name(username) not in AI_NAMES:
            print("LOGOUT", username)
            print(this_is_ai_name(username))
            room_id = db_user.current_room_id
            db_user.is_active = False
            db.commit()

            if room_id:
                users = room_manager.get_client_users_in_room(db, room_id)
                room = room_manager.get_room_by_id(db, room_id)
                if room:
                    for user in users:
                        if user.username != username:
                            if user.username in sockets:
                                socketio.emit(
                                    "player_left_room",
                                    {
                                        "message": f"{this_is_ai_name(username)} elhagyta a szobát",
                                        "left_player": username,
                                        "players": [u.model_dump() for u in users],
                                        "max_player_count": room.max_player_count,
                                    },
                                    to=sockets[user.username],
                                )

                    room_manager.update_room_player_count(db, room_id)
                    room_manager.broadcast_room_list_update(db)

    sockets.pop(username, None)
    session.pop("username", None)
    session.pop("socket_id", None)


@socketio.on("disconnect")
def handle_disconnect() -> None:
    username = session.get("username")
    if not username:
        return

    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if db_user and this_is_ai_name(username) not in AI_NAMES:
            print("DISCONNECT", username)
            print(this_is_ai_name(username))
            room_id = db_user.current_room_id
            db_user.is_active = False
            db.commit()

            if room_id:
                users = room_manager.get_client_users_in_room(db, room_id)
                room = room_manager.get_room_by_id(db, room_id)
                if room:
                    socketio.emit(
                        "player_left_room",
                        {
                            "message": f"{this_is_ai_name(username)} elhagyta a szobát",
                            "left_player": username,
                            "players": [u.model_dump() for u in users],
                            "max_player_count": room.max_player_count,
                        },
                        room=room_id,
                    )
                    room_manager.update_room_player_count(db, room_id)
                    room_manager.broadcast_room_list_update(db)

    sockets.pop(username, None)
    session.pop("username", None)
    session.pop("socket_id", None)


@socketio.on("get_user_stats")
def handle_get_user_stats(data: dict) -> None:
    username = data.get("username")
    if not username:
        return

    with get_db_session() as db:
        try:
            total_games = (
                db.query(DBGame)
                .join(DBGame.players)
                .filter(DBUser.username == username, DBGame.game_status == "end")
                .count()
            )

            won_games = (
                db.query(DBGame)
                .join(DBGame.players)
                .filter(
                    DBUser.username == username,
                    DBGame.game_status == "end",
                    DBGame.loser_username != username,
                )
                .count()
            )

            emit(
                "user_stats",
                {
                    "username": username,
                    "total_games": total_games,
                    "won_games": won_games,
                },
            )

        except Exception as e:
            print(f"Error getting user stats: {e}")
            emit("user_stats", {"username": username, "total_games": 0, "won_games": 0})


@socketio.on("leave_room")
def handle_leave_room(data: dict) -> None:
    print(f"LEAVE ROOM{data['username']}")
    username = session.get("username")
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if data.get("reconnecting", False):
            db_user.is_active = True
            db.commit()
        if not db_user or not db_user.current_room_id:
            return

        room_id = db_user.current_room_id
        target_room = room_manager.get_room_by_id(db, room_id)

        if not target_room:
            return

        room_manager.remove_user_from_room(db, username)

        leave_room(room_id)
        emit("left_room", {"message": "Szoba elhagyás"})

        users = room_manager.get_client_users_in_room(db, room_id)

        socketio.emit(
            "player_left_room",
            {
                "message": f"{this_is_ai_name(username)} elhagyta a szobát",
                "left_player": username,
                "players": [u.model_dump() for u in users],
                "max_player_count": target_room.max_player_count,
            },
            room=room_id,
        )

        room_manager.broadcast_room_list_update(db)


@socketio.on("create_room")
def create_room(data: dict) -> None:
    username = session.get("username")
    with get_db_session() as db:
        password = None
        if data["password_protected"]:
            password = data["password"]

        db_room = room_manager.create_room(
            db,
            room_name=data["room_name"],
            max_player_count=data["max_player_count"],
            password=password,
        )

        join_user_to_room(db_room.room_id, username, skip_password_check=True)
        room_manager.broadcast_room_list_update(db)


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


def join_user_to_room(
    room_id: str, username: str, skip_password_check: bool = False
) -> None:
    with get_db_session() as db:
        target_room = room_manager.get_room_by_id(db, room_id)
        if not target_room:
            return

        success = room_manager.join_user_to_room(db, room_id, username)
        if not success:
            return

        join_room(room_id)
        room_joined()
        room_manager.broadcast_room_list_update(db)

        users = room_manager.get_client_users_in_room(db, room_id)
        room_model = room_manager.get_room_model(db, room_id)

        socketio.emit(
            "room_players_updated",
            {
                "room": room_model.model_dump(),
                "players": [u.model_dump() for u in users],
            },
            room=room_id,
        )

        room_users = room_manager.get_room_users(db, room_id)
        if len(room_users) >= target_room.max_player_count:
            players = [
                {"username": user.username, "is_active": user.is_active}
                for user in room_users
            ]

            socketio.emit(
                "start_game",
                {"players": [player["username"] for player in players]},
                room=room_id,
            )

            game_manager.start_game(db, players, room_id)
            room_manager.broadcast_room_list_update(db)


def room_joined() -> None:
    username = session.get("username")
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user or not db_user.current_room_id:
            return

        current_room = room_manager.get_room_by_id(db, db_user.current_room_id)
        if not current_room:
            return

        players = []
        room_users = room_manager.get_room_users(db, db_user.current_room_id)
        for user in room_users:
            players.append({"username": user.username, "is_active": user.is_active})

        emit(
            "joined_room",
            {
                "room_id": current_room.room_id,
                "name": current_room.name,
                "players": players,
                "username": username,
                "max_player_count": current_room.max_player_count,
            },
            to=request.sid,
        )


def get_user_room_id(username: str) -> Optional[str]:
    db_user = get_user_by_username(username)
    return db_user.current_room_id if db_user else None


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)
    with get_db_session() as db:
        try:
            db_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
            if not db_room:
                return

            db_game = None
            for game in db_room.games:
                if game.game_status == "run":
                    db_game = game
                    break

            if not db_game:
                return

            game_instance = game_manager.get_game_instance(room_id)
            if not game_instance:
                return

            client_game_state = data.get("game_state", {})
            statement = data.get("statement", "")
            passing = data.get("pass", False)

            for card in Animal:
                if card.value == client_game_state["question_card"]:
                    game_instance.select_card(card, passing)

            game_instance.select_target_player(client_game_state["targeted_player"])

            if (
                game_instance.state.active_player.username
                not in game_instance.state.visited_already
            ):
                game_instance.state.visited_already.add(
                    game_instance.state.active_player.username
                )

            if (
                "active_player" in client_game_state
                and client_game_state["active_player"]
            ):
                active_player_name = client_game_state["active_player"]
                for player in game_instance.state.players:
                    if player.username == active_player_name:
                        game_instance.state.active_player = player
                        break

            game_instance.make_statement(statement)

            game_manager.send_game_state_to_players(
                db, game_instance, room_id, hide_card_for_unvisited=True
            )
            if game_manager.is_ai_player(game_instance.state.targeted_player.username):
                game_manager.ai_guess(db, game_instance, room_id)
        except Exception as e:
            print(f"Error in handle_oke_click: {e}")


@socketio.on("guess")
def handle_guess(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)
    game_instance = game_manager.get_game_instance(room_id)

    if not game_instance:
        return

    guess = data["guess"]
    game_manager.ai_handle_guess_internal(
        get_db_session(), guess, game_instance, room_id
    )


def send_game_state_to_all_players(game_instance, room_id, show_card=False):
    hide_card = not show_card
    game_manager.send_game_state_to_players(
        get_db_session(), game_instance, room_id, hide_card_for_unvisited=hide_card
    )


@socketio.on("pass")
def handle_pass() -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)

    if not username or not room_id:
        return

    game_instance = game_manager.get_game_instance(room_id)
    if not game_instance:
        return

    with get_db_session() as db:
        if game_instance.state.targeted_player is not None:
            next_player = game_instance.state.targeted_player
            game_instance.state.active_player = next_player
            game_instance.state.targeted_player = None

        if game_instance.has_4_cards_in_front():
            game_manager.game_end(room_id, db)
            return

        game_manager.send_game_state_to_players(
            db, game_instance, room_id, hide_card_for_unvisited=False
        )

        if all_players_active_in_room(room_id):
            active_player_name = game_instance.state.active_player.username
            base_name = this_is_ai_name(active_player_name)

            if base_name in AI_NAMES:
                game_manager.ai_activity(db, game_instance, room_id, True)


@socketio.on("add_ai_player")
def add_ai_player(data: dict) -> None:
    room_id = data.get("room_id")
    if not room_id:
        emit("join_room_error", {"message": "Szoba ID hiányzik"}, to=request.sid)
        return

    with get_db_session() as db:
        try:
            target_room = room_manager.get_room_by_id(db, room_id)
            if not target_room:
                emit(
                    "join_room_error",
                    {"message": "Szoba nem található"},
                    to=request.sid,
                )
                return

            room_users = room_manager.get_room_users(db, room_id)
            existing_names = {user.username for user in room_users}

            if len(room_users) >= target_room.max_player_count:
                emit("join_room_error", {"message": "A szoba megtelt"}, to=request.sid)
                return

            ai_username = get_available_ai_name(existing_names, room_id)
            create_ai_user_in_db(ai_username)
            print(f"AI player added: {ai_username}")
            join_user_to_room(room_id, ai_username, skip_password_check=True)
            room_manager.broadcast_room_list_update(db)

        except Exception as e:
            print(f"Error adding AI player: {e}")
            emit(
                "join_room_error",
                {"message": "AI játékos hozzáadása sikertelen"},
                to=request.sid,
            )


def ai_pass(game_instance=None, room_id=None):
    game_manager.ai_pass_internal(get_db_session(), game_instance, room_id)


def this_is_ai_name(name: str) -> str:
    for ai_name in AI_NAMES:
        if name.startswith(ai_name):
            return ai_name

    return name


def initialize_server_data():
    create_tables()
    game_manager.load_existing_games(get_db_session())
    cleanup_inactive_users()


def cleanup_inactive_users():
    with get_db_session() as db:
        try:
            active_users = db.query(DBUser).filter(DBUser.is_active).all()
            inactive_count = 0

            for user in active_users:
                if this_is_ai_name(user.username) not in AI_NAMES:
                    user.is_active = False
                    inactive_count += 1

            db.commit()
        except Exception as e:
            print(f"Hiba a felhasználók tisztítása során: {e}")


def create_ai_user_in_db(ai_username: str) -> DBUser:
    with get_db_session() as db:
        existing_ai = db.query(DBUser).filter(DBUser.username == ai_username).first()
        if existing_ai:
            return existing_ai
        ai_user = DBUser(
            username=ai_username,
            password="ai_password",
            is_active=True,
        )
        db.add(ai_user)
        db.commit()
        return ai_user


def get_available_ai_name(existing_players: Set[str], room_id) -> str:
    used_base_names = set()
    for player_name in existing_players:
        base_name = this_is_ai_name(player_name)
        if base_name in AI_NAMES:
            used_base_names.add(base_name)

    available_names = [name for name in AI_NAMES if name not in used_base_names]

    base_name = random.choice(available_names)
    return f"{base_name}_{room_id}"


if __name__ == "__main__":
    initialize_server_data()
    socketio.run(app, debug=False, host="0.0.0.0")
