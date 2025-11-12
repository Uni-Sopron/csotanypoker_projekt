from typing import Optional
from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from csotanypoker.models.user import (
    Client_User,
    AI_NAMES,
    is_ai_player,
    this_is_ai_name,
)
from csotanypoker.server.database import DBUser, DBRoom, DBGame, get_db_session
from csotanypoker.server.room_manager import RoomManager
from csotanypoker.server.game_manager import GameManager
from csotanypoker.server.password_manager import hash_password, verify_password
from csotanypoker.server.server_helper import get_user_room_id, initialize_server_data

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY", "titkos_kulcs")
socketio = SocketIO(app, cors_allowed_origins="*")

sockets = {}
game_instances = {}
room_manager = RoomManager(socketio, sockets)
game_manager = GameManager(socketio, sockets, room_manager)


def handle_user_join_to_room(
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

        notify_user_joined_room()
        room_manager.broadcast_room_list_update(db)

        users = room_manager.get_client_users_in_room(db, room_id)
        room_model = room_manager.get_room_model(db, room_id)

        socketio.emit(
            "room_players_updated",
            {
            
                "players": [u.model_dump() for u in users],
            },
            room=room_id,
        )

        room_users = room_manager.get_room_users(db, room_id)
        if len(room_users) >= target_room.max_player_count:
            
            players = room_manager.get_players_list(db, room_id)
            socketio.emit(
                "start_game",
                {"players": [player.username for player in players]},
                room=room_id,
            )

            game_manager.start_game(db,[player.username for player in players], room_id)
            room_manager.broadcast_room_list_update(db)


def notify_user_joined_room() -> None:
    username = session.get("username")
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user or not db_user.current_room_id:
            return

        current_room = room_manager.get_room_by_id(db, db_user.current_room_id)
        if not current_room:
            return

      
        room_users = room_manager.get_room_users(db, db_user.current_room_id)
        players = [
            Client_User(username=user.username, is_active=user.is_active) 
            for user in room_users
        ]
        emit(
            "joined_room",
            {
                "room_id": current_room.room_id,
                "room_name": current_room.name,  
                "players": [p.model_dump() for p in players],

                "max_player_count": current_room.max_player_count,
            },
            to=request.sid,
        )


@socketio.on("connect")
def handle_connect() -> None:
    print(f"Kliens csatlakozott: {request.sid}")


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

    hashed_password = hash_password(password)
    new_db_user = DBUser(username=username, password=hashed_password, is_active=False)
    db.add(new_db_user)
    db.commit()
    db.close()

    handle_login({"username": username, "password": password})

@socketio.on("rejoin_waiting_room")
def handle_start_new_game(data: dict) -> None:
    username = session.get("username")
    if not username:
        print("Nincs username a session-ben")
        return

    with get_db_session() as db:
        db_user: Optional[DBUser] = (
            db.query(DBUser).filter(DBUser.username == username).first()
        )

        if not db_user or not db_user.current_room_id:
            print(f"Felhasználó nem aktív vagy nincs szobája: {username}")
            return

        room_id = db_user.current_room_id
        target_room = room_manager.get_room_by_id(db, room_id)

        if not target_room:
            print(f"Szoba nem található: {room_id}")
            return
        target_game = (
            db.query(DBGame)
            .filter(DBGame.room_id == room_id, DBGame.game_status == "run")
            .first()
        )

        db_user.is_active = True
        db.commit()

        sockets[username] = request.sid
        session["socket_id"] = request.sid

        join_room(room_id)

        room_manager.update_room_player_count(db, room_id)
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
                "players": [u.model_dump() for u in users], 
            },
            room=room_id,
        )

        room_users = room_manager.get_room_users(db, room_id)
        player_usernames = [user.username for user in room_users]

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

            game_manager.start_game(db, player_usernames, room_id)

        room_manager.broadcast_room_list_update(db)

@socketio.on("all_players_leave_room")
def handle_all_players_leave_room(data) -> None:
    room_id = data["room_id"]
    current_username = session.get("username")
    room_manager.remove_all_users_from_room(
        room_id, current_username, data.get("reconnecting", False)
    )


@socketio.on("vote_rematch")
def handle_vote_rematch(data: dict) -> None:
    room_id = data["room_id"]
    username = data["username"]

    with get_db_session() as db:
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not target_room:
            return

        game_instance = game_manager.get_game_instance(room_id)
        if game_instance:
            game_instance.state.voters.add(username)

        room_users = room_manager.get_room_users(db, room_id)
        if (
            len(game_instance.state.voters)
            + sum(
                1
                for player in game_instance.state.players
                if is_ai_player(player.username)
            )
            == target_room.max_player_count
        ):
            players = room_manager.get_players_list(db, room_id)
            socketio.emit(
                "start_game",
                {"players": [player.username for player in players]},
                room=room_id,
            )

            game_instance.state.voters.clear()

            if room_id in game_instances:
                del game_instances[room_id]

            for game in target_room.games:
                if game.game_status == "run":
                    game.game_status = "end"
            db.commit()

            game_manager.start_game(db, [player.username for player in players], room_id)
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

        if not verify_password(password, dbuser.password):
            emit("login_error", {"message": "Hibás jelszó."})
            return

        if dbuser.is_active:
            emit("login_error", {"message": "Ez a felhasználó már be van jelentkezve."})
            return

        dbuser.is_active = True
        db.commit()

        session["username"] = username
        session["socket_id"] = request.sid

        sockets[username] = request.sid

        previous_room_id = dbuser.current_room_id
        previous_room = (
            db.query(DBRoom).filter(DBRoom.room_id == previous_room_id).first()
            if previous_room_id
            else None
        )

        rooms_data = room_manager.get_rooms_data()
        user = Client_User(username=username, is_active=True)

        if previous_room and previous_room_id:
            dbuser.is_active = False
            db.commit()
            previous_room_model = room_manager.get_room_model(db, previous_room_id)

            emit(
                "reconnect_offer",
                {
                    "username": username,
                    "rooms": rooms_data,
                    "previous_room": previous_room_model.model_dump() if previous_room_model else None, 
                    "game_start": room_manager.game_is_running(db, previous_room_id),
                },
                to=sockets[username],
            )

            return
        else:
            emit("login_success", {"user": user.model_dump(), "rooms": rooms_data})
@socketio.on("disconnect")
def handle_disconnect() -> None:
    username = session.get("username")
    _handle_user_disconnect(username, send_success_message=False)


@socketio.on("logout")
def handle_logout(data) -> None:
    username = data.get("username") or session.get("username")
    _handle_user_disconnect(username, send_success_message=True)


def _handle_user_disconnect(username: str, send_success_message: bool = False) -> None:
    if not username:
        return

    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if db_user and not is_ai_player(username):
            print(f"LOGOUT: {username}")
            room_id = db_user.current_room_id

            db_user.is_active = False
            db.commit()

            if room_id:
                leave_room(room_id)
                print(f"{username} elhagyta a SocketIO room-ot: {room_id}")

                users = room_manager.get_client_users_in_room(db, room_id)
                room = room_manager.get_room_by_id(db, room_id)
                if room:
                    socketio.emit(
                        "player_left_room",
                        {
                            "message": f"{this_is_ai_name(username)} inaktív lett",
                            "players": [u.model_dump() for u in users],
                        },
                        room=room_id,
                    )
                    room_manager.update_room_player_count(db, room_id)
                    room_manager.broadcast_room_list_update(db)

    sockets.pop(username, None)

    session.clear()
    print(f"Session törölve: {username}")


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
    username = data.get("username")
    if not username:
        username = session.get("username")

    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()

        if not db_user or not db_user.current_room_id:
            return

        if data.get("reconnecting", False):
            db_user.is_active = True
            db.commit()

        room_id = db_user.current_room_id
        target_room = room_manager.get_room_by_id(db, room_id)

        if not target_room:
            return

        is_ai = is_ai_player(username)

        room_manager.remove_user_from_room(db, username)
        if not is_ai:
            leave_room(room_id)
            emit("left_room", {"message": "Szoba elhagyás"})
        else:
            db.delete(db_user)
            db.commit()

        users = room_manager.get_client_users_in_room(db, room_id)
    
        socketio.emit(
            "player_left_room",
            {
                "message": f"{this_is_ai_name(username)} elhagyta a szobát",
                "players": [u.model_dump() for u in users],

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

        handle_user_join_to_room(db_room.room_id, username, skip_password_check=True)
        room_manager.broadcast_room_list_update(db)


@socketio.on("join_room")
def join_room_request(data: dict) -> None:
    username = session.get("username")
    room_id = data["room_id"]
    provided_password = data.get("password", "")
    skipp_password_check = data["skipp_password"]

    if skipp_password_check or room_manager.validate_room_password(
        room_id, provided_password
    ):
        handle_user_join_to_room(room_id, username)
    else:
        emit("join_room_error", {"message": "Helytelen jelszó"}, to=request.sid)


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)
    with get_db_session() as db:
        game_manager.handle_oke_click(db, username, room_id, data)


@socketio.on("guess")
def handle_guess(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)
    game_instance = game_manager.get_game_instance(room_id)

    if not game_instance:
        return

    guess = data["guess"]
    game_manager._process_guess(
        get_db_session(),
        game_instance,
        room_id,
        guess,
    )


@socketio.on("pass")
def handle_pass(data: dict) -> None:
    username = session.get("username")
    room_id = get_user_room_id(username)

    if not username or not room_id:
        return

    game_instance = game_manager.get_game_instance(room_id)
    if not game_instance:
        return

    with get_db_session() as db:
        game_instance.state.passing = True
        if game_instance.state.targeted_player is not None:
            next_player = game_instance.state.targeted_player
            game_instance.state.active_player = next_player
            game_instance.state.targeted_player = None
            game_instance.state.passing = True

        if game_manager._check_and_handle_game_end(db, game_instance, room_id):
            return

        game_manager.send_game_state_to_players(
            db, game_instance, room_id, hide_card_for_unvisited=False
        )

        if room_manager.all_players_active_in_room(room_id):
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

            ai_username = room_manager.get_available_ai_name(existing_names, room_id)
            room_manager.create_ai_user_in_db(ai_username)
            handle_user_join_to_room(room_id, ai_username, skip_password_check=True)
            room_manager.broadcast_room_list_update(db)

        except Exception as e:
            print(f"Error adding AI player: {e}")
            emit(
                "join_room_error",
                {"message": "AI játékos hozzáadása sikertelen"},
                to=request.sid,
            )


if __name__ == "__main__":
    initialize_server_data(game_manager)
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app, debug=False, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True
    )
