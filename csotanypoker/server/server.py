import os
import uuid
from typing import Optional, List
import random
from typing import Set
from flask import Flask, json, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy.orm import Session, sessionmaker

from csotanypoker.models.animal import Animal
from csotanypoker.models.player import VisiblePlayer, OpponentPlayer
from csotanypoker.server.game_background import GameLogic
from csotanypoker.models.gamestate import ClientGameState, GameState
from csotanypoker.models.room import Room
from csotanypoker.models.user import Client_User, AI_NAMES
from csotanypoker.server.database import (
    engine,
    DBUser,
    DBRoom,
    DBGame,
    create_tables,
)

app = Flask(__name__)
app.secret_key = "titkos_kulcs"  # Secret key needed for session handling
socketio = SocketIO(app, cors_allowed_origins="*")

sockets = {}
game_instances = {}


def all_players_active_in_room(room_id: str) -> bool:
    """Check if all players in a room are currently active"""
    with get_db_session() as db:
        room_users = get_room_users(room_id)
        if not room_users:
            return False

        for user in room_users:
          
            db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
            if not db_user or not db_user.is_active:
                print(f"Player {user.username} is not active")
                return False

        print(f"All {len(room_users)} players in room {room_id} are active")
        return True


def get_db_session():
    Session = sessionmaker(bind=engine)
    return Session()


def get_user_by_username(username: str) -> Optional[DBUser]:
    with get_db_session() as db:
        return db.query(DBUser).filter(DBUser.username == username).first()


def get_room_by_id(room_id: str) -> Optional[DBRoom]:
    with get_db_session() as db:
        return db.query(DBRoom).filter(DBRoom.room_id == room_id).first()


def get_room_users(room_id: str) -> List[DBUser]:
    with get_db_session() as db:
        users = db.query(DBUser).filter(DBUser.current_room_id == room_id).all()
        return users


def update_room_player_count(room_id: str):
    with get_db_session() as db:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if room:
            user_count = (
                db.query(DBUser).filter(DBUser.current_room_id == room_id).count()
            )
            room.player_count = user_count
            db.commit()


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
        update_room_player_count(room_id)

        print(f"szoba id: {room_id}, szoba neve: {target_room.name}")

        room_users = get_room_users(room_id)

        if len(room_users) >= target_room.max_player_count:
            player_usernames = [user.username for user in room_users]

            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )
            print("rejoin_waiting_room: Játék indul a szobában:", room_id)
            start_game(player_usernames, room_id, reconnect=True)

        resume_ai_activity_if_needed(room_id)


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
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
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
        update_room_player_count(room_id)

        print(f"szoba id: {room_id}, szoba neve: {target_room.name}")

        room_users = get_room_users(room_id)
        users = [
            Client_User(username=r_u.username, is_active=r_u.is_active)
            for r_u in room_users
        ]

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

        player_usernames = [user.username for user in room_users]

        print("JATEKOSSZAM", len(room_users))
        if len(room_users) >= target_room.max_player_count:
            if target_game:
                game_instance = get_game_instance(room_id)
                if game_instance:
                    send_game_state_to_players(
                        game_instance, room_id, hide_card_for_unvisited=True
                    )
                    resume_ai_activity_if_needed(room_id)

                    return
            player_usernames = [user.username for user in room_users]
            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )

            print("rejoin_waiting_room: Játék indul a szobában:", room_id)
            start_game(player_usernames, room_id)

        broadcast_room_list_update()


@socketio.on("all_players_leave_room")
def handle_all_players_leave_room(data) -> None:
    room_id = data["room_id"]
    remove_all_users_from_room(room_id)


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

        game_instance = get_game_instance(room_id)
        if game_instance:
            game_instance.state.voters.add(username)

        room_users = get_room_users(room_id)
        if (
            len(game_instance.state.voters)
            + sum(
                1
                for player in game_instance.state.players
                if is_ai_player(player.username)
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

            start_game(players, room_id)
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


def get_rooms_data():
    db = get_db_session()
    rooms_data = {}
    rooms = db.query(DBRoom).all()

    for room in rooms:
        player_count = user_counter(room.room_id)
        has_running_game = game_is_start(room_id=room.room_id)

        has_human = has_human_player_in_room(room.room_id)

        if not has_running_game and player_count != 0 and has_human:
            rooms_data[room.room_id] = {
                "name": room.name,
                "max_player_count": room.max_player_count,
                "password_protected": True if room.password else False,
                "player_count": player_count,
            }

    db.close()
    return rooms_data


def has_human_player_in_room(room_id: str) -> bool:
    """Check if a room has at least one human (non-AI) player"""

    room_users = get_room_users(room_id)
    for user in room_users:
        if not is_ai_player(user.username):
            return True
    return False


def game_is_start(room_id: int) -> bool:
    with get_db_session() as db:
        running_game = (
            db.query(DBGame)
            .filter(DBGame.room_id == room_id, DBGame.game_status == "run")
            .first()
        )
        return running_game is not None


def broadcast_room_list_update():
    rooms_data = get_rooms_data()
    with get_db_session() as db:
        users_not_in_room = (
            db.query(DBUser)
            .filter(DBUser.current_room_id == None, DBUser.is_active == True)
            .all()
        )

        for user in users_not_in_room:
            if user.username in sockets:
                user_socket_id = sockets[user.username]
                try:
                    socketio.emit(
                        "rooms_updated", {"rooms": rooms_data}, to=user_socket_id
                    )
                except Exception as e:
                    print(e)
                    sockets.pop(user.username, None)


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
                room_users = get_room_users(room_id)
                users = [
                    Client_User(username=r_u.username, is_active=r_u.is_active)
                    for r_u in room_users
                ]
                room = get_room_by_id(room_id)
                if room:
                    for user in users:
                        if user.username != username:
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

                    update_room_player_count(room_id)
                    broadcast_room_list_update()

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
                room_users = get_room_users(room_id)
                users = [
                    Client_User(username=r_u.username, is_active=r_u.is_active)
                    for r_u in room_users
                ]
                room = get_room_by_id(room_id)
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
                    update_room_player_count(room_id)
                    broadcast_room_list_update()

    sockets.pop(username, None)
    session.pop("username", None)
    session.pop("socket_id", None)


def remove_all_users_from_room(room_id: str) -> None:
    with get_db_session() as db:
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if not target_room:
            return

        room_users = get_room_users(room_id)

        for user in room_users:
            dbuser = db.query(DBUser).filter(DBUser.username == user.username).first()
            dbuser.is_active = True
            db.commit()
            if dbuser:
                dbuser.current_room_id = None

                if user.username in sockets and dbuser.is_active:
                    try:
                        socketio.emit(
                            "left_room",
                            {"message": "Szoba elhagyás"},
                            to=sockets[user.username],
                        )
                        leave_room(room_id)
                    except Exception as e:
                        print(e)
                        sockets.pop(user.username, None)

        db.commit()
        update_room_player_count(room_id)
        broadcast_room_list_update()


@socketio.on("leave_room")
def handle_leave_room(data: dict) -> None:
    print(f"LEAVE ROOM{data['username']}")
    username = session.get("username")
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        db_user.is_active = True
        db.commit()
        if not db_user or not db_user.current_room_id:
            return

        room_id = db_user.current_room_id
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if not target_room:
            return

        db_user.current_room_id = None
        db.commit()
        update_room_player_count(room_id)

        leave_room(room_id)
        emit("left_room", {"message": "Szoba elhagyás"})
        room_users = get_room_users(room_id)
        users = [
            Client_User(username=r_u.username, is_active=r_u.is_active)
            for r_u in room_users
        ]

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

        broadcast_room_list_update()


@socketio.on("create_room")
def create_room(data: dict) -> None:
    username = session.get("username")
    with get_db_session() as db:
        while True:
            room_id = uuid.uuid4().hex[:15]
            existing = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
            if not existing:
                break

        password = None
        if data["password_protected"]:
            password = data["password"]

        db_room = DBRoom(
            room_id=room_id,
            name=data["room_name"],
            max_player_count=data["max_player_count"],
            password=password,
            password_protected=bool(password),
        )

        db.add(db_room)
        db.commit()

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
    with get_db_session() as db:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not room:
            return False

        if not room.password:
            return True

        return room.password == provided_password


def join_user_to_room(
    room_id: str, username: str, skip_password_check: bool = False
) -> None:
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if not db_user or not target_room:
            return

        db_user.current_room_id = room_id
        db.commit()
        update_room_player_count(room_id)

        join_room(room_id)
        room_joined()
        broadcast_room_list_update()

        room_users = get_room_users(room_id)

        users = [
            Client_User(username=r_u.username, is_active=r_u.is_active)
            for r_u in room_users
        ]

        room = Room(
            room_id=room_id,
            name=target_room.name,
            max_player_count=target_room.max_player_count,
            password_protected=bool(target_room.password),
            player_count=len(room_users),
        )
        socketio.emit(
            "room_players_updated",
            {
                "room": room.model_dump(),
                "players": [u.model_dump() for u in users],
            },
            room=room_id,
        )

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

            start_game(players, room_id)
            broadcast_room_list_update()


def room_joined() -> None:
    username = session.get("username")
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user or not db_user.current_room_id:
            return

        current_room = (
            db.query(DBRoom).filter(DBRoom.room_id == db_user.current_room_id).first()
        )
        if not current_room:
            return

        room_users = get_room_users(db_user.current_room_id)
        players = []
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


def get_game_instance(room_id: str) -> Optional[GameLogic]:
    return game_instances.get(room_id)


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

            game_instance = get_game_instance(room_id)
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

            send_game_state_to_players(
                game_instance, room_id, hide_card_for_unvisited=True
            )
            if is_ai_player(game_instance.state.targeted_player.username):
                ai_guess(game_instance, room_id)
        except Exception as e:
            print(f"Error in handle_oke_click: {e}")
            
            
def reset_callback(nextplayer, game_instance=None, room_id=None, db=None):
    for player in game_instance.state.players:
        player.statement = None
        player.is_true = None

    game_instance.state.active_player = nextplayer

    if game_instance.has_cards_in_hand():
        print("Game ended - no cards in hand")
        game_end(room_id, db)
        return

    if game_instance.has_4_cards_in_front():
        print("Game ended - 4 cards in front")
        game_end(room_id, db)
        return

    game_instance.state.question_card = None
    game_instance.state.targeted_player = None
    game_instance.state.visited_already = set()

    send_game_state_to_all_players_sync(game_instance, room_id)

    ai_activity(game_instance, room_id)

@socketio.on("guess")
def handle_guess(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)
    game_instance = get_game_instance(room_id)

    if not game_instance:
        return

    guess = data["guess"]
    ai_handle_guess_internal(guess, game_instance, room_id)


def send_game_state_to_all_players_sync(game_instance, room_id):
    send_game_state_to_players(game_instance, room_id, hide_card_for_unvisited=True)


def send_game_state_to_players(
    game_instance, room_id, hide_card_for_unvisited=True, message=""
):
    with get_db_session() as db:
        try:
            active_users = (
                db.query(DBUser)
                .filter(DBUser.current_room_id == room_id, DBUser.is_active == True)
                .all()
            )
            active_usernames = {user.username for user in active_users}

            for player in game_instance.state.players:
                if player.username in active_usernames:
                    player_sid = sockets.get(player.username)
                    if is_ai_player(player.username):
                        send_game_state_to_players_with_ai(
                            game_instance,
                            room_id,
                            hide_card_for_unvisited,
                            message,
                        )
                    else:
                        if player_sid:
                            _send_game_state_to_single_player(
                                game_instance,
                                player,
                                player_sid,
                                hide_card_for_unvisited,
                                message,
                            )
                        else:
                            print(f"No socket ID found for player: {player.username}")

        except Exception as e:
            print(f"Error in send_game_state_to_players: {e}")


def _send_game_state_to_single_player(
    game_instance, player, player_sid, hide_card_for_unvisited, message
):
    try:
        client_game_state = send_client_game_state(game_instance)

        if (
            hide_card_for_unvisited
            and game_instance.state.question_card
            and player.username not in game_instance.state.visited_already
            and game_instance.state.targeted_player is not None
        ):
            client_game_state["question_card"] = "card_back"
            print(f"Player {player.username} sees card_back (not visited yet)")
        else:
            print(f"Player {player.username} sees actual card")

        visible_player_data = send_main_visible_player(player)

        opponent_players_data = [
            send_opponent_player(p)
            for p in game_instance.state.players
            if p.username != player.username
        ]

        payload = {
            "game_state": client_game_state,
            "visible_player_data": visible_player_data,
            "opponent_players_data": opponent_players_data,
            "message": message,
        }

        try:
            json.dumps(payload)
        except (TypeError, ValueError) as e:
            print(f"JSON serialization error for {player.username}: {e}")
            return

        socketio.emit("Game_state", payload, to=player_sid)

    except Exception as e:
        print(f"Error sending game state to {player.username}: {e}")


def send_game_state_to_all_players(game_instance, room_id, show_card=False):
    hide_card = not show_card
    send_game_state_to_players(
        game_instance, room_id, hide_card_for_unvisited=hide_card
    )


@socketio.on("pass")
def handle_pass() -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)

    if not username or not room_id:
        return

    game_instance = get_game_instance(room_id)
    if not game_instance:
        return

    ai_pass_internal(game_instance, room_id)


@socketio.on("add_ai_player")
def add_ai_player(data: dict) -> None:
    room_id = data.get("room_id")
    if not room_id:
        emit("error", {"message": "Room ID required"})
        return

    with get_db_session() as db:
        try:
            target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
            if not target_room:
                emit("error", {"message": "Room not found"})
                return

            room_users = get_room_users(room_id)
            existing_names = {user.username for user in room_users}

            if len(room_users) >= target_room.max_player_count:
                emit("error", {"message": "Room is full"})
                return

            ai_username = get_available_ai_name(existing_names, room_id)
            create_ai_user_in_db(ai_username)
            join_user_to_room(room_id, ai_username, skip_password_check=True)
            broadcast_room_list_update()

        except Exception as e:
            print(f"Error adding AI player: {e}")


def game_end(room_id: str, db: Session = None) -> None:
    should_close_db = False
    if db is None:
        db = get_db_session()
        should_close_db = True

    try:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not room:
            return

        game_instance = get_game_instance(room_id)
        if not game_instance:
            return

        loser_name = game_instance.state.active_player.username

        running_game = None
        for game in room.games:
            if game.game_status == "run":
                running_game = game
                break

        if running_game:
            running_game.loser_username = loser_name
            running_game.game_status = "end"  
            print(f"Game {running_game.game_id} ended. Loser saved: {loser_name}")
        else:
            print(f"Warning: No running game found in room {room_id}")

        db.commit()

        socketio.emit(
            "game_over",
            {
                "losing_player": loser_name,
            },
            room=room_id,
        )

        print(f"Game ended in room {room_id}. Loser: {loser_name}")

    finally:
        if should_close_db:
            db.close()


def start_game(players: list, room_id: str, reconnect: bool = False) -> None:
    global game_instances
    print(f"START GAME {players} {room_id} RECONNECT: {reconnect}")
    with get_db_session() as db:
        db_room = db.query(DBRoom).filter_by(room_id=room_id).first()
        if not db_room:
            print(f"Room not found: {room_id}")
            return

        if reconnect:
            print("RECONNECT JÁTÉK INDÍTÁSA")
            if room_id in game_instances:
                game_instance = game_instances[room_id]
                send_game_state_to_players(
                    game_instance, room_id, hide_card_for_unvisited=True
                )
            else:
                try:
                    existing_game = None
                    for game in db_room.games:
                        if game.game_status == "run":
                            existing_game = game
                            break

                    if existing_game:
                        save_path = f"csotanypoker/server/games_saves/game_{existing_game.game_id}.pkl"
                        loaded_state = GameState.load_from_file(save_path)

                        if loaded_state:
                            game_logic = GameLogic(
                                existing_game.game_id,
                                list(loaded_state.players),
                                room_id=room_id,
                            )
                            game_logic.state = loaded_state
                            game_instances[room_id] = game_logic

                            send_game_state_to_players(
                                game_logic, room_id, hide_card_for_unvisited=True
                            )
                        else:
                            print(f"Failed to load game state, creating new game")
                            reconnect = False
                except Exception as e:
                    print(f"Error during reconnect: {e}")
                    reconnect = False

            if reconnect:
                return

        if not reconnect:
            print("ÚJ JÁTÉK INDUL")

            existing_game = None
            for game in db_room.games:
                if game.game_status == "run":
                    existing_game = game
                    break

            if existing_game:
                print(f"A running game already exists for room {room_id}")
                return

            unique_game_id = str(uuid.uuid4())

            try:
                game_instances[room_id] = GameLogic(
                    unique_game_id,
                    [VisiblePlayer(username=str(user["username"])) for user in players],
                    room_id=room_id,
                )
                game_instance = game_instances[room_id]

                db_game = DBGame(
                    game_id=unique_game_id,
                    game_status="run",
                    loser_username=None,
                    room_id=room_id,
                )
                db.add(db_game)
                db.commit()

                for player in players:
                    username = (
                        player["username"] if isinstance(player, dict) else player
                    )
                    db_user = (
                        db.query(DBUser).filter(DBUser.username == username).first()
                    )
                    if db_user:
                        db_game.players.append(db_user)

                db.commit()
                print(
                    f"Players added to game: {[p['username'] if isinstance(p, dict) else p for p in players]}"
                )

                save_success = game_instance.state.manual_save()
                if save_success:
                    print("Game state pickle file created successfully")
                else:
                    print("Warning: Failed to create pickle file")

                send_game_state_to_players(
                    game_instance, room_id, hide_card_for_unvisited=False
                )
                ai_activity(game_instance, room_id)

            except Exception as e:
                print(f"Error creating new game: {e}")


def execute_ai_move(game_instance, ai_game_state, statement, passing):
    room_id = game_instance.state.room_id
    if not all_players_active_in_room(room_id):
        return

    socketio.sleep(2.0)
    with app.test_request_context():
        session["username"] = game_instance.state.active_player.username
        handle_oke_click(
            {
                "game_state": ai_game_state,
                "statement": statement,
                "pass": passing,
            }
        )


def resume_ai_activity_if_needed(room_id: str):
    game_instance = get_game_instance(room_id)
    if not game_instance or not game_instance.state.active_player:
        return

    active_player_name = game_instance.state.active_player.username
    base_name = this_is_ai_name(active_player_name)

    if base_name in AI_NAMES and all_players_active_in_room(room_id):
        has_question_card = game_instance.state.question_card is not None
        has_targeted_player = game_instance.state.targeted_player is not None

        if has_question_card and has_targeted_player:
            targeted_player_name = game_instance.state.targeted_player.username
            targeted_base_name = this_is_ai_name(targeted_player_name)
            if targeted_base_name in AI_NAMES:
                with app.test_request_context():
                    session["username"] = targeted_player_name
                    ai_guess(game_instance, room_id)
                return
            else:
                return

        elif has_question_card and not has_targeted_player:
            with app.test_request_context():
                session["username"] = active_player_name
                ai_pass_internal(game_instance, room_id)
            return

        elif not has_question_card:
            print(f"Resuming AI activity for {active_player_name} - no active round")
            ai_activity(game_instance, room_id)
        else:
            print(f"AI {active_player_name} ")


def send_client_game_state(game_instance):
    return ClientGameState(
        game_id=game_instance.state.game_id,
        room_id=game_instance.state.room_id,
    
        visited_already=game_instance.state.visited_already,
        voters=game_instance.state.voters,
        active_player=game_instance.state.active_player.username,
        targeted_player=game_instance.state.targeted_player.username
        if game_instance.state.targeted_player
        else None,
        question_card=game_instance.state.question_card,
    ).model_dump()

def ai_handle_guess_internal(guess, game_instance, room_id):
    with get_db_session() as db:
        try:
            result = game_instance.check_truth(guess)

            if result:
                nextplayer = game_instance.place_card(game_instance.state.active_player)
            else:
                nextplayer = game_instance.place_card(
                    game_instance.state.targeted_player
                )

        
            game_instance.state.visited_already = set(
                player.username for player in game_instance.state.players
            )

            send_game_state_to_all_players_sync(game_instance, room_id)

            socketio.start_background_task(
                target=lambda: (
                    socketio.sleep(3),
                    reset_callback(nextplayer, game_instance, room_id, db),
                )
            )

        except Exception as e:
            print(f"Error in ai_handle_guess_internal: {e}")


def ai_pass(game_instance=None, room_id=None):
    ai_pass_internal(game_instance, room_id)


def ai_guess(game_instance=None, room_id=None):
    if not all_players_active_in_room(room_id):
        return

    if len(game_instance.state.visited_already) < (
        len(game_instance.state.players) - 1
    ):
        tipp = random.choice([True, False, "pass"])
    else:
        tipp = random.choice([True, False])

    socketio.sleep(3.0)
    if tipp == "pass":
        ai_pass_internal(game_instance, room_id)
    else:
        ai_handle_guess_internal(tipp, game_instance, room_id)


def ai_pass_internal(game_instance, room_id):
    with get_db_session() as db:
        if game_instance.state.targeted_player is not None:
            game_instance.state.active_player = game_instance.state.targeted_player
            game_instance.state.targeted_player = None

        if game_instance.has_4_cards_in_front():
            game_end(room_id, db)
            return

        send_game_state_to_players(
            game_instance, room_id, hide_card_for_unvisited=False
        )

        if all_players_active_in_room(room_id):
            ai_activity(game_instance, room_id, True)


def this_is_ai_name(name: str) -> str:
    for ai_name in AI_NAMES:
        if name.startswith(ai_name):
            return ai_name

    return name


def ai_activity(game_instance, room_id, passing=False):
    if not game_instance.state.active_player:
        return

    active_player_name = game_instance.state.active_player.username
    base_name = this_is_ai_name(active_player_name)

    if base_name not in AI_NAMES:
        return

    if not all_players_active_in_room(room_id):
        return

    try:
        if not passing:
            if not game_instance.state.active_player.cards_in_hand:
                return

            selected_card = random.choice(
                game_instance.state.active_player.cards_in_hand
            )
        else:
            selected_card = game_instance.state.question_card

        other_players = [
            p
            for p in game_instance.state.players
            if p.username != game_instance.state.active_player.username
        ]

        available_targets = [
            p
            for p in other_players
            if p.username not in game_instance.state.visited_already
        ]

        if not available_targets:
            available_targets = other_players

        if not available_targets:
            return

        target_player = random.choice(available_targets)
        statement = random.choice(list(Animal)).value

        ai_game_state = {
            "question_card": selected_card.value,
            "targeted_player": target_player.username,
            "active_player": game_instance.state.active_player.username,
        }

        socketio.start_background_task(
            execute_ai_move, game_instance, ai_game_state, statement, passing
        )

    except Exception as e:
        print(f"Error in ai_activity: {e}")


def send_main_visible_player(player_data):
    return player_data.model_dump()


def send_opponent_player(player_data):
    return OpponentPlayer(
        username=player_data.username,
        cards_in_front=player_data.cards_in_front,
        statement=player_data.statement,
        is_true=player_data.is_true,
        card_count_int=len(player_data.cards_in_hand),
    ).model_dump()


def load_existing_games():
    global game_instances
    with get_db_session() as db:
        try:
            running_games = db.query(DBGame).filter(DBGame.game_status == "run").all()

            print(f"Talált {len(running_games)} futó játék az adatbázisban")

            for db_game in running_games:
                try:
                    save_path = (
                        f"csotanypoker/server/games_saves/game_{db_game.game_id}.pkl"
                    )

                    if not os.path.exists(save_path):
                        continue

                    loaded_state = GameState.load_from_file(save_path)

                    if loaded_state:
                        db_players = db_game.players
                        players = []
                        for db_player in db_players:
                            loaded_player = None
                            for p in loaded_state.players:
                                if p.username == db_player.username:
                                    loaded_player = p
                                    break

                            if loaded_player:
                                players.append(loaded_player)
                            else:
                                players.append(
                                    VisiblePlayer(username=db_player.username)
                                )

                        game_logic = GameLogic(
                            db_game.game_id,
                            players,
                            room_id=db_game.room_id,
                            from_db=True,
                        )

                        game_instances[db_game.room_id] = game_logic

                except Exception as game_error:
                    print(
                        f"Hiba a játék betöltése során ({db_game.game_id}): {game_error}"
                    )

        except Exception as e:
            print(f" hiba a játékok betöltése során: {e}")


def initialize_server_data():
    create_tables()
    load_existing_games()
    cleanup_inactive_users()


def cleanup_inactive_users():
    """Tisztítja az inaktív felhasználókat szerver újraindítás után"""
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
    available_names = [name for name in AI_NAMES if name not in existing_players]
    base_name = f"{random.choice(available_names)}_{room_id}"
    return base_name


def is_ai_player(username: str) -> bool:
    base_name = this_is_ai_name(username)
    return base_name in AI_NAMES


def send_game_state_to_players_with_ai(
    game_instance, room_id, hide_card_for_unvisited=True, message=""
):
    with get_db_session() as db:
        try:
            active_users = (
                db.query(DBUser)
                .filter(DBUser.current_room_id == room_id, DBUser.is_active is True)
                .all()
            )
            active_usernames = {user.username for user in active_users}

            for player in game_instance.state.players:
                if player.username in active_usernames:
                    if is_ai_player(player.username):
                        print(f"AI player {player.username} would make decision here")
                    else:
                        player_sid = sockets.get(player.username)
                        if player_sid and not player_sid.startswith("ai_"):
                            _send_game_state_to_single_player(
                                game_instance,
                                player,
                                player_sid,
                                hide_card_for_unvisited,
                                message,
                            )
                        else:
                            print(
                                f"No valid socket ID found for player: {player.username}"
                            )

        except Exception as e:
            print(f"Error in send_game_state_to_players_with_ai: {e}")


if __name__ == "__main__":
    initialize_server_data()
    socketio.run(app, debug=False, host="0.0.0.0")
