import atexit
import signal
import sys
import uuid
from typing import Optional, List

from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

from sqlalchemy.orm import Session

from csotanypoker.models.player import Player
from csotanypoker.server.game_background import GameLogic

from csotanypoker.server.database import (
    engine,
    Base,
    DBUser,
    DBRoom,
    Game,
    create_tables,
)

app = Flask(__name__)
app.secret_key = "titkos_kulcs"  # Secret key needed for session handling
socketio = SocketIO(app, cors_allowed_origins="*")

sockets = {}
game_instances = {}


def get_db_session():
    """Adatbázis session létrehozása"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    return Session()


def reset_database():  # this is only needed for testing
    Base.metadata.drop_all(bind=engine)  # deletes all tables
    Base.metadata.create_all(bind=engine)


def get_active_users():
    """Get all active users from database"""
    db = get_db_session()
    try:
        active_users = db.query(DBUser).filter(DBUser.is_active == True).all()
        return active_users
    finally:
        db.close()


def set_all_users_inactive():
    db = get_db_session()
    try:
        active_users = db.query(DBUser).filter(DBUser.is_active == True).all()

        for user in active_users:
            print(f"Logging out user: {user.username}")
            handle_logout({"username": user.username})

        print("All users set to inactive successfully")
    except Exception as e:
        print(f"Error setting users inactive: {e}")
    finally:
        db.close()


def cleanup_on_shutdown():
    set_all_users_inactive()
    print("Cleanup completed")


def signal_handler(signum, frame):
    cleanup_on_shutdown()
    sys.exit(0)


def get_user_by_username(username: str) -> Optional[DBUser]:
    db = get_db_session()
    try:
        user = db.query(DBUser).filter(DBUser.username == username).first()
        return user
    finally:
        db.close()


def get_room_by_id(room_id: str) -> Optional[DBRoom]:
    db = get_db_session()
    try:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        return room
    finally:
        db.close()


def get_room_users(room_id: str) -> List[DBUser]:
    db = get_db_session()
    try:
        users = db.query(DBUser).filter(DBUser.current_room_id == room_id).all()
        return users
    finally:
        db.close()


def add_user_to_room_association(username: str, room_id: str):
    db = get_db_session()
    try:
        user = db.query(DBUser).filter(DBUser.username == username).first()
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if user and room:
            if room not in user.rooms_in:
                user.rooms_in.append(room)
                db.commit()
                print(f"Added {username} to room {room_id} in association table")
    finally:
        db.close()


def update_user_activity(username: str, is_active: bool):
    db = get_db_session()
    try:
        user = db.query(DBUser).filter(DBUser.username == username).first()
        if user:
            user.is_active = is_active
            db.commit()
    finally:
        db.close()


def update_user_room(username: str, room_id: Optional[str]):
    db = get_db_session()
    try:
        user = db.query(DBUser).filter(DBUser.username == username).first()
        if user:
            user.current_room_id = room_id
            db.commit()
    finally:
        db.close()


def update_room_player_count(room_id: str):
    db = get_db_session()
    try:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if room:
            user_count = (
                db.query(DBUser).filter(DBUser.current_room_id == room_id).count()
            )
            room.player_count = user_count
            db.commit()
    finally:
        db.close()


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

    new_db_user = DBUser(username=username, password=password, is_active=False)
    db.add(new_db_user)
    db.commit()
    db.close()

    handle_login({"username": username, "password": password})


@socketio.on("rejoin_waiting_room")
def handle_start_new_game(data: dict):
    username = session.get("username")

    if not username:
        print("Nincs bejelentkezett felhasználó a session-ben")
        return
    if username not in sockets:
        print(f"Nincs aktív socket kapcsolat {username} felhasználóhoz")
        return

    db: Session = get_db_session()

    try:
        db_user: Optional[DBUser] = (
            db.query(DBUser)
            .filter(DBUser.username == username, DBUser.is_active == True)
            .first()
        )

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
        active_users = get_active_users()
        room_users = get_room_users(room_id)
        print([u.username for u in active_users])

        socketio.emit(
            "rejoin_waiting_success",
            {
                "room_id": room_id,
                "room_name": target_room.name,
                "players": [u.username for u in room_users],
                "activ_users": [u.username for u in active_users],
                "max_player_count": target_room.max_player_count,
                "password": target_room.password if target_room.password else None,
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

        print("JATEKOSSZAM", len(room_users))
        if len(room_users) >= target_room.max_player_count:
            player_usernames = [user.username for user in room_users]

            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )
            print("rejoin_waiting_room: Játék indul a szobában:", room_id)
            start_game(player_usernames, room_id)

        broadcast_room_list_update()
    finally:
        db.close()


@socketio.on("rejoin_game")
def handle_rejoin_game(data: dict) -> None:
    username = data.get("username")
    room_id = data.get("room_id")

    if not username:
        print("Nincs felhasználónév megadva")
        return

    sockets[username] = request.sid
    session["username"] = username
    session["socket_id"] = request.sid

    print("Rejoin game request received for room:", room_id)

    db = get_db_session()
    try:
        db_user = (
            db.query(DBUser)
            .filter(DBUser.username == username, DBUser.is_active == True)
            .first()
        )

        if not db_user:
            print(f"Felhasználó nem aktív: {username}")
            return

        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not target_room:
            return

        print(f"Szoba megtalálva: {target_room.name}, {target_room.room_id}")

        room_users = get_room_users(room_id)
        active_users = get_active_users()

        for user in room_users:
            update_user_room(user.username, target_room.room_id)
            print(f"Játékos: {user.username, user.current_room_id, user.is_active}")

        if room_id in game_instances:
            active_usernames = [u.username for u in active_users]

            for player in game_instances[room_id].state.players:
                user = db.query(DBUser).filter(DBUser.username == player.name).first()
                print(
                    f"Játékos a játékban: {player.name, user.is_active if user else 'NOT FOUND'}"
                )
                print(f"Játékos kártyái: {player.cards_in_hand}")
                print(f"Játékos kártyái elől: {player.cards_in_front}")

            jatekosok = [
                player.name for player in game_instances[room_id].state.players
            ]
            aktiv_jatekos = game_instances[room_id].state.active_player.name

            aktual_game_state = {
                "room_id": target_room.room_id,
                "activ_users": active_usernames,
                "max_player_count": target_room.max_player_count,
                "active_player": aktiv_jatekos,
                "players": jatekosok,
            }

            emit(
                "rejoin_game_success",
                {
                    "username": username,
                    "previous_room_id": target_room.room_id,
                    "room_name": target_room.name,
                    "game_state": aktual_game_state,
                },
                to=sockets[username],
            )

            player_data = {}
            for player in game_instances[room_id].state.players:
                user = db.query(DBUser).filter(DBUser.username == player.name).first()
                player_data[player.name] = {
                    "cards_in_front": player.cards_in_front,
                    "card_count": len(player.cards_in_hand),
                    "is_active": user.is_active if user else False,
                }

            active_usernames_set = set(active_usernames)
            for player in game_instances[room_id].state.players:
                if player.name in active_usernames_set and player.name in sockets:
                    player_sid = sockets.get(player.name)
                    if player_sid:
                        cards_in_hand = [k.name for k in player.cards_in_hand]
                        try:
                            emit(
                                "player_data",
                                {
                                    "name": player.name,
                                    "cards_in_hand": cards_in_hand,
                                    "starting_player": game_instances[
                                        room_id
                                    ].state.active_player.name,
                                    "player_data": player_data,
                                },
                                to=player_sid,
                            )
                        except Exception as e:
                            print(f"Hiba üzenet küldése során {player.name}-nak: {e}")
                            sockets.pop(player.name, None)

            print("handle_rejoin_game: Játékos újracsatlakozott a szobához:", room_id)
            start_game(aktual_game_state["players"], target_room.room_id, True)
    finally:
        db.close()


@socketio.on("all_players_leave_room")
def handle_all_players_leave_room(data) -> None:
    """
    Handle all players leaving the room.
    This function resets the room state and notifies all players.
    """
    room_id = data["room_id"]
    remove_all_users_from_room(room_id)


@socketio.on("vote_rematch")
def handle_vote_rematch(data: dict) -> None:
    print("Szavazás a visszavágóra:", data)
    room_id = data["room_id"]
    username = data["username"]

    db = get_db_session()
    try:
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not target_room:
            return

        print(f"Szobanév: {target_room.name}")

        game_instance = get_game_instance(room_id)
        if game_instance:
            game_instance.state.voters.add(username)

        room_users = get_room_users(room_id)
        if len(game_instance.state.voters) >= target_room.max_player_count:
            print(f"Új játék indul a szobában: {room_id}")
            print(f"szobák: {game_instances}")

            player_usernames = [user.username for user in room_users]
            socketio.emit(
                "start_game",
                {
                    "message": "Új játék kezdődik!",
                    "players": player_usernames,
                    "room_id": room_id,
                    "game_ids": [game.id for game in target_room.game_ids],
                },
                room=room_id,
            )
            game_instance.state.voters = []
            print("handle_vote_rematch: Játék újraindítása a szobában:", room_id)
            start_game(player_usernames, room_id)
        else:
            print(f"Szavazás érkezett a szobában: {room_id}")
            socketio.emit(
                "rematch_vote_received",
                {"voters": list(game_instance.state.voters), "room_id": room_id},
                room=room_id,
            )
    finally:
        db.close()


@socketio.on("login")
def handle_login(data: dict) -> None:
    db: Session = get_db_session()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    try:
        if not username or not password:
            emit("login_error", {"message": "Felhasználónév és jelszó nem lehet üres."})
            return

        dbuser: Optional[DBUser] = (
            db.query(DBUser).filter(DBUser.username == username).first()
        )

        if not dbuser or dbuser.password != password:
            emit("login_error", {"message": "Hibás felhasználónév vagy jelszó."})
            return

        if dbuser.is_active:
            emit("login_error", {"message": "Ez a felhasználó már be van jelentkezve."})
            return

        dbuser.is_active = True
        db.commit()

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

        emit("login_success", {"username": username, "rooms": rooms_data})

        if previous_room:
            rooms_data = {}
            all_rooms = db.query(DBRoom).all()
            for room in all_rooms:
                rooms_data[room.room_id] = {
                    "name": room.name,
                    "player_count": room.max_player_count,
                    "password_protected": True if room.password else False,
                    "actual_player_count": room.player_count,
                    "game_ids": [game.id for game in room.game_ids],
                }

            user_in_room = dbuser.current_room_id == previous_room_id
            if user_in_room:
                emit(
                    "reconnect_offer",
                    {
                        "username": username,
                        "rooms": rooms_data,
                        "previous_room_id": previous_room.room_id,
                    },
                    to=sockets[username],
                )
                return
            else:
                dbuser.current_room_id = None
                db.commit()
    finally:
        db.close()


def get_rooms_data():
    db = get_db_session()

    rooms_data = {}

    rooms = db.query(DBRoom).all()
    for room in rooms:
        print("Jatékosok száma a szobában:", room.player_count)
        if room.player_count != 0 and room.game_ids == []:
            rooms_data[room.room_id] = {
                "name": room.name,
                "player_count": room.max_player_count,
                "password_protected": True if room.password else False,
                "actual_player_count": room.player_count,
            }
    db.close()
    return rooms_data


def broadcast_room_list_update():
    rooms_data = get_rooms_data()
    db = get_db_session()

    try:
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
                    print(f"Hiba üzenet küldése során {user.username}-nak: {e}")

                    sockets.pop(user.username, None)
    finally:
        db.close()


@socketio.on("logout")
def handle_logout(data) -> None:
    print("Kliens kijelenткezett")
    username = data.get("username")
    if not username:
        username = session.get("username")

    if not username:
        return

    update_user_activity(username, False)

    sockets.pop(username, None)

    db_user = get_user_by_username(username)
    if db_user and db_user.current_room_id:
        room_users = get_room_users(db_user.current_room_id)
        active_users = get_active_users()
        room = get_room_by_id(db_user.current_room_id)
        if room:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in room_users],
                    "activ_users": [u.username for u in active_users],
                    "max_player_count": room.max_player_count,
                },
                room=db_user.current_room_id,
            )

    session.pop("username", None)
    session.pop("socket_id", None)


@socketio.on("disconnect")
def handle_disconnect() -> None:
    print("Kliens lecsatlakozott")
    username = session.get("username")
    if not username:
        return
    update_user_activity(username, False)
    sockets.pop(username, None)

    db_user = get_user_by_username(username)
    if db_user and db_user.current_room_id:
        room_users = get_room_users(db_user.current_room_id)
        active_users = get_active_users()
        room = get_room_by_id(db_user.current_room_id)
        if room:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in room_users],
                    "activ_users": [u.username for u in active_users],
                    "max_player_count": room.max_player_count,
                },
                room=db_user.current_room_id,
            )

    session.pop("username", None)
    session.pop("socket_id", None)


def remove_all_users_from_room(room_id: str) -> None:
    db: Session = get_db_session()
    print(f"Removing all users from room {room_id}")

    try:
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if not target_room:
            return

        room_users = get_room_users(room_id)

        for user in room_users:
            dbuser = db.query(DBUser).filter(DBUser.username == user.username).first()
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
                        sockets.pop(user.username, None)

        db.commit()
        update_room_player_count(room_id)
        broadcast_room_list_update()
    finally:
        db.close()


@socketio.on("leave_room")
def handle_leave_room(data: dict) -> None:
    """
    Handle user leaving a room
    """
    db: Session = get_db_session()
    print(f"LEAVE ROOM{data['username']}")
    username = session.get("username")

    try:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user or not db_user.current_room_id:
            return

        room_id = db_user.current_room_id
        target_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

        if not target_room:
            return

        game_ids = [game.id for game in target_room.game_ids]
        if game_ids and room_id in game_instances:
            active_games = (
                db.query(Game)
                .filter(Game.id.in_(game_ids), Game.game_status == "run")
                .all()
            )

            if active_games:
                remove_all_users_from_room(room_id)
                return

        db_user.current_room_id = None
        db.commit()
        update_room_player_count(room_id)

        leave_room(room_id)
        emit("left_room", {"message": "Szoba elhagyás"})

        room_users = get_room_users(room_id)
        active_users = get_active_users()
        socketio.emit(
            "player_left_room",
            {
                "message": f"{username} elhagyta a szobát",
                "left_player": username,
                "players": [u.username for u in room_users],
                "activ_users": [u.username for u in active_users],
                "max_player_count": target_room.max_player_count,
            },
            room=room_id,
        )

        broadcast_room_list_update()
    finally:
        db.close()


@socketio.on("create_room")
def create_room(data: dict) -> None:
    db: Session = get_db_session()
    username = session.get("username")

    try:
        room_id: str = str(uuid.uuid4())

        password = None
        if data["password_protected"]:
            password = data["password"]

        db_room = DBRoom(
            room_id=room_id,
            name=data["room_name"],
            max_player_count=data["max_player_count"],
            password=password,
            password_protected=bool(password),
            player_count=0,
        )

        db.add(db_room)
        db.commit()

        join_user_to_room(room_id, username, skip_password_check=True)
        broadcast_room_list_update()
    finally:
        db.close()


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
    db = get_db_session()
    try:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not room:
            return False

        if not room.password:
            return True

        return room.password == provided_password
    finally:
        db.close()


def join_user_to_room(
    room_id: str, username: str, skip_password_check: bool = False
) -> None:
    db: Session = get_db_session()

    try:
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
        active_users = get_active_users()
        socketio.emit(
            "room_players_updated",
            {
                "room_id": room_id,
                "players": [u.username for u in room_users],
                "activ_users": [u.username for u in active_users],
                "max_player_count": target_room.max_player_count,
            },
            room=room_id,
        )

        if len(room_users) >= target_room.max_player_count:
            player_usernames = [user.username for user in room_users]

            socketio.emit(
                "start_game",
                {"players": player_usernames},
                room=room_id,
            )
            print("join_user_to_room: Játék indul a szobában:", room_id)
            start_game(player_usernames, room_id)
            broadcast_room_list_update()
    finally:
        db.close()


def room_joined() -> None:
    db: Session = get_db_session()
    username = session.get("username")

    try:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user or not db_user.current_room_id:
            return

        current_room = (
            db.query(DBRoom).filter(DBRoom.room_id == db_user.current_room_id).first()
        )
        if not current_room:
            return

        room_users = get_room_users(db_user.current_room_id)
        player_names = [u.username for u in room_users]

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
    finally:
        db.close()


def get_user_room_id(username: str) -> Optional[str]:
    db_user = get_user_by_username(username)
    return db_user.current_room_id if db_user else None


def get_game_instance(room_id: str) -> Optional[GameLogic]:
    return game_instances.get(room_id)


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid
    username = session.get("username")
    room_id = get_user_room_id(username)

    try:
        db_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not db_room:
            return

        db_game = None
        for game in db_room.game_ids:
            if game.game_status == "run":
                db_game = game
                break

        if not db_game:
            return

        game_instance = get_game_instance(room_id)

        for card in game_instance.state.deck:
            if card.name == data["selected_card"]:
                game_instance.state.question_card = card
                break

        game_instance.select_target_player(data["selected_player"])
        game_instance.make_statement(statement=data["set_card_giver"])

        if not data["pass"]:
            if game_instance.has_cards_in_hand():
                game_end(room_id, db)
                return
            game_instance.select_card(
                selected_card_id=game_instance.state.question_card.name
            )

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

        active_users = (
            db.query(DBUser)
            .filter(DBUser.current_room_id == room_id, DBUser.is_active == True)
            .all()
        )

        active_usernames = {user.username for user in active_users}

        for j in game_instance.state.players:
            player_sid = sockets.get(j.name)
            if (
                player_sid
                and j.name in game_instance.state.question_card.visited_already
                and j.name != game_instance.state.targeted_player.name
                and j.name in active_usernames
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
    finally:
        db.close()


def card_content(room_id: str):
    db: Session = get_db_session()
    try:
        db_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not db_room:
            return

        db_game = None
        for game in db_room.game_ids:
            if game.game_status == "run":
                db_game = game
                break

        if not db_game:
            return

        game_instance = get_game_instance(room_id)

        if game_instance and game_instance.state.question_card:
            socketio.emit(
                "card_content",
                {
                    "card_type": game_instance.state.question_card.type,
                    "card_index": game_instance.state.question_card.index,
                    "visited_by": game_instance.state.question_card.visited_already,
                },
                room=room_id,
            )
    finally:
        db.close()


@socketio.on("guess")
def handle_guess(data: dict) -> None:
    db: Session = get_db_session()
    try:
        username = session.get("username")
        room_id = get_user_room_id(username)

        db_user = (
            db.query(DBUser)
            .filter(
                DBUser.username == username,
                DBUser.current_room_id == room_id,
                DBUser.is_active == True,
            )
            .first()
        )

        if not db_user:
            return

        db_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not db_room:
            return

        db_game = None
        for game in db_room.game_ids:
            if game.game_status == "run":
                db_game = game
                break

        if not db_game:
            return

        game_instance = get_game_instance(room_id)

        guess = data["guess"]
        result = game_instance.check_truth(guess)
        card_content(room_id)

        if result:
            game_instance.place_card(game_instance.state.active_player)
        else:
            game_instance.place_card(game_instance.state.targeted_player)

        place_card(room_id, db)

    finally:
        db.close()


@socketio.on("pass")
def handle_pass(data: dict) -> None:
    db: Session = get_db_session()
    try:
        sid = request.sid
        username = session.get("username")
        room_id = get_user_room_id(username)

        db_user = (
            db.query(DBUser)
            .filter(
                DBUser.username == username,
                DBUser.current_room_id == room_id,
                DBUser.is_active == True,
            )
            .first()
        )

        if not db_user:
            return

        db_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not db_room:
            return

        db_game = None
        for game in db_room.game_ids:
            if game.game_status == "run":
                db_game = game
                break

        if not db_game:
            return

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

    finally:
        db.close()


def place_card(room_id: str, db: Session = None) -> None:
    should_close_db = False
    if db is None:
        db = get_db_session()
        should_close_db = True

    try:
        db_room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not db_room:
            return

        db_game = None
        for game in db_room.game_ids:
            if game.game_status == "run":
                db_game = game
                break

        if not db_game:
            return

        game_instance = get_game_instance(room_id)
        room_users = db.query(DBUser).filter(DBUser.current_room_id == room_id).all()

        user_lookup = {user.username: user for user in room_users}
        player_data = {}
        for j in game_instance.state.players:
            db_user = user_lookup.get(j.name)
            is_user_active = db_user.is_active if db_user else False

            player_data[j.name] = {
                "cards_in_front": j.cards_in_front,
                "card_count": len(j.cards_in_hand),
                "is_active": is_user_active,
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

        active_users = {u.username for u in room_users if u.is_active}

        for j in game_instance.state.players:
            if j.name in active_users:
                player_sid = sockets.get(j.name)
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
            game_end(room_id, db)

    finally:
        if should_close_db:
            db.close()


def game_end(room_id: str, db: Session = None) -> None:
    should_close_db = False
    if db is None:
        db = get_db_session()
        should_close_db = True

    try:
        room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()
        if not room:
            return

        db_game = None
        for game in room.game_ids:
            if game.game_status == "run" and game.loser_username is None:
                db_game = game
                break

        if not db_game:
            return

        game_instance = get_game_instance(room_id)
        if not game_instance:
            return

        loser_name = game_instance.state.active_player.name
        game_instance.state.loser_username = loser_name
        game_instance.state.game_status = "end"

        db_game.loser_username = loser_name
        db_game.game_status = "end"

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
    db = get_db_session()

    try:
        db_room = db.query(DBRoom).filter_by(room_id=room_id).first()
        if not db_room:
            print(f"Room not found: {room_id}")
            return

        if reconnect:
            print("RECONNECT JÁTÉK INDÍTÁSA")

            db_game = None
            for game in db_room.game_ids:
                if game.game_status == "run":
                    db_game = game
                    break

            if not db_game:
                print("No running game found in database for reconnection")
                return

            if room_id in game_instances:
                game_instance = game_instances[room_id]
                print(f"Reconnecting to existing game in room {room_id}")

                active_users = (
                    db.query(DBUser).filter(DBUser.current_room_id == room_id).all()
                )

                user_lookup = {user.username: user for user in active_users}

                active_name = game_instance.state.active_player.name
                player_data = {}
                for j in game_instance.state.players:
                    db_user = user_lookup.get(j.name)
                    is_user_active = db_user.is_active if db_user else False

                    player_data[j.name] = {
                        "cards_in_front": j.cards_in_front,
                        "card_count": len(j.cards_in_hand),
                        "is_active": is_user_active,
                    }

                active_usernames = {u.username for u in active_users if u.is_active}

                for j in game_instance.state.players:
                    if j.name in active_usernames:
                        player_sid = sockets.get(j.name)
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

                if game_instance.state.question_card:
                    for j in game_instance.state.players:
                        if (
                            j.name in active_usernames
                            and j.name
                            in game_instance.state.question_card.visited_already
                        ):
                            player_sid = sockets.get(j.name)
                            if player_sid:
                                emit(
                                    "card_content",
                                    {
                                        "card_type": game_instance.state.question_card.type,
                                        "card_index": game_instance.state.question_card.index,
                                        "visited_by": game_instance.state.question_card.visited_already,
                                    },
                                    to=player_sid,
                                )
                return
        else:
            print("ÚJ JÁTÉK INDUL")

            existing_game = None
            for game in db_room.game_ids:
                if game.game_status == "run":
                    existing_game = game
                    break

            if existing_game:
                print(f"A running game already exists for room {room_id}")
                return

            unique_game_id = str(uuid.uuid4())
            print(f"Egyedi játék ID: {unique_game_id}")

            game_instances[room_id] = GameLogic(
                unique_game_id, [Player(name=str(user)) for user in players]
            )
            game_instance = game_instances[room_id]
            print("Játék példány létrehozva:", game_instances[room_id])

            db_game = Game(
                id=game_instance.state.id, game_status="run", loser_username=None
            )
            db.add(db_game)

            db_room.game_ids.append(db_game)
            for player_name in players:
                add_user_to_room_association(player_name, room_id)

            db.commit()
            print(
                f"Új játék létrehozva és hozzárendelve a szobához: {db_game.id} → {room_id}"
            )

            room_users = (
                db.query(DBUser).filter(DBUser.current_room_id == room_id).all()
            )

            user_lookup = {user.username: user for user in room_users}

            active_name = game_instance.state.active_player.name
            player_data = {}
            for j in game_instance.state.players:
                db_user = user_lookup.get(j.name)
                is_user_active = db_user.is_active if db_user else False

                player_data[j.name] = {
                    "cards_in_front": j.cards_in_front,
                    "card_count": len(j.cards_in_hand),
                    "is_active": is_user_active,
                }

            active_usernames = {u.username for u in room_users if u.is_active}

            for j in game_instance.state.players:
                if j.name in active_usernames:
                    player_sid = sockets.get(j.name)
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

    finally:
        db.close()


signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
atexit.register(cleanup_on_shutdown)

if __name__ == "__main__":
    # reset_database()
    create_tables()
    socketio.run(app, debug=True, host="0.0.0.0")
