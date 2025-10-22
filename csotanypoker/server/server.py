from typing import Optional
from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy.orm import Session
from csotanypoker.models.animal import Animal
from dotenv import load_dotenv  
import os
from csotanypoker.models.user import Client_User, AI_NAMES, this_is_ai_name
from csotanypoker.server.database import (
    DBUser,
    DBRoom,
    DBGame,
    get_db_session
)
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


def notify_user_joined_room() -> None:
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
        db_user: Optional[DBUser] = db.query(DBUser).filter(DBUser.username == username).first()
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

        room_users = room_manager.get_room_users(room_id)

        if len(room_users) >= target_room.max_player_count:
            player_usernames = [user.username for user in room_users]

            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )
            game_manager.start_game(db, player_usernames, room_id, reconnect=True)

        game_manager.resume_ai_activity_if_needed(db, room_id)


@socketio.on("rejoin_waiting_room")
def handle_start_new_game():
    username = session.get("username")
    if not username:
        print("Nincs username a session-ben")
        return
    
   

    with get_db_session() as db:
        db_user: Optional[DBUser] = db.query(DBUser).filter(DBUser.username == username).first()
        
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
    room_manager.remove_all_users_from_room(room_id, current_username, data.get("reconnecting", False))


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
            emit("login_error", {"message": "Felhasználónév és jelszó nem lehet üres."})
            return

        dbuser: Optional[DBUser] =db.query(DBUser).filter(DBUser.username == username).first()
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
            previous_room_data = {}
            all_rooms = db.query(DBRoom).all()
            for room in all_rooms:
                if room.room_id == previous_room_id:
                    room_player_count = room_manager.user_counter(room.room_id)
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
                    "game_start": room_manager.game_is_running(db, previous_room_id),
                },
                to=sockets[username],
            )

            return
        else:
            emit("login_success", {"user": user.model_dump(), "rooms": rooms_data})



@socketio.on("logout")
def handle_logout(data) -> None:
    username = data.get("username")
    if not username:
        username = session.get("username")

    if not username:
        return

    with get_db_session() as db:
        db_user =db.query(DBUser).filter(DBUser.username == username).first()
        if db_user and this_is_ai_name(username) not in AI_NAMES:
            print(f"LOGOUT: {username}")
            room_id = db_user.current_room_id
            
            # USER INAKTIVÁLÁSA
            db_user.is_active = False
            db.commit()

            # HA SZOBÁBAN VAN, ELHAGYJA A SOCKETIO ROOM-OT
            if room_id:
                # SocketIO room elhagyása
                leave_room(room_id)
                print(f"{username} elhagyta a SocketIO room-ot: {room_id}")
                
                # Értesítés a többieknek
                users = room_manager.get_client_users_in_room(db, room_id)
                room = room_manager.get_room_by_id(db, room_id)
                if room:
                    socketio.emit(
                        "player_left_room",
                        {
                            "message": f"{this_is_ai_name(username)} inaktív lett",
                            "left_player": username,
                            "players": [u.model_dump() for u in users],
                            "max_player_count": room.max_player_count,
                        },
                        room=room_id,  # Csak az aktív usereknek megy
                    )
                    room_manager.update_room_player_count(db, room_id)
                    room_manager.broadcast_room_list_update(db)

    # SOCKET MAPPING TÖRLÉSE
    sockets.pop(username, None)
    
    # SESSION TELJES TISZTÍTÁSA
    session.clear()  # Ez törli az ÖSSZES session adatot
    print(f"Session törölve: {username}")
    
    # LOGOUT MEGERŐSÍTÉS
    emit("logout_success", {"message": "Sikeres kijelentkezés"})



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

        is_ai = this_is_ai_name(username) in AI_NAMES

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

        handle_user_join_to_room(db_room.room_id, username, skip_password_check=True)
        room_manager.broadcast_room_list_update(db)


@socketio.on("join_room")
def join_room_request(data: dict) -> None:
    username = session.get("username")
    room_id = data["room_id"]
    provided_password = data.get("password", "")
    skipp_password_check = data["skipp_password"]

    if skipp_password_check or room_manager.validate_room_password(room_id, provided_password):
        handle_user_join_to_room(room_id, username)
    else:
        emit("join_room_error", {"message": "Helytelen jelszó"}, to=request.sid)



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
    socketio.run(app, debug=False, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)