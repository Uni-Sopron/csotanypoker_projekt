import uuid
from typing import Optional

from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

from sqlalchemy.orm import Session

from csotanypoker.models.player import Player
from csotanypoker.models.room import Room
from csotanypoker.models.user import User
from csotanypoker.server.game_background import GameLogic


from csotanypoker.server.database import (
    engine,
    Base,
    DBUser,
    DBRoom,
    Game,
    room_user_association,
)

app = Flask(__name__)
app.secret_key = "titkos_kulcs"  # Secret key needed for session handling
socketio = SocketIO(app, cors_allowed_origins="*")


sockets = {}

ROOMS = {}
USERS = {}

game_instances = {}


def get_db_session():
    """Adatbázis session létrehozása"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    return Session()


def reset_database():  # this is only needed for testing
    Base.metadata.drop_all(bind=engine)  # deletes all tables
    Base.metadata.create_all(bind=engine)


def syncronise_user_db(user: User):
    db = get_db_session()
    try:
        db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
        if db_user:
            db_user.current_room_id = user.current_room_id
            db_user.is_active = user.is_active
        else:
            db_user = DBUser(
                username=user.username,
                password=user.password,
                current_room_id=user.current_room_id,
                is_active=user.is_active,
            )
            db.add(db_user)
        db.commit()
    finally:
        db.close()


def syncronise_room_db(room: Room):
    db = get_db_session()
    try:
        db_room = db.query(DBRoom).filter(DBRoom.room_id == room.room_id).first()
        if db_room:
            db_room.name = room.name
            db_room.password = room.password
            db_room.password_protected = bool(room.password)
            db_room.max_player_count = room.max_player_count
            db_room.player_count = len(room.users)
        else:
            db_room = DBRoom(
                room_id=room.room_id,
                name=room.name,
                password=room.password,
                password_protected=bool(room.password),
                max_player_count=room.max_player_count,
                player_count=len(room.users),
            )
            db.add(db_room)
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

    new_user = User(username=username, password=password, is_active=False)
    USERS[username] = new_user

    new_db_user = DBUser(username=username, password=password)
    db.add(new_db_user)
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
    target_room = ROOMS.get(room_id)

    if not target_room:
        db.close()
        return

    user = USERS.get(username)
    if user and user not in target_room.users:
        target_room.users.append(user)
        user.current_room_id = room_id

    join_room(room_id)
    syncronise_room_db(target_room)

    print(f"szoba id: {room_id}, szoba neve: {target_room.name}")
    print([u.username for u in USERS.values() if u.is_active])

    socketio.emit(
        "rejoin_waiting_success",
        {
            "room_id": room_id,
            "room_name": target_room.name,
            "players": [u.username for u in target_room.users],
            "activ_users": [u.username for u in USERS.values() if u.is_active],
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

    print("JATEKOSSZAM", len(target_room.users))
    if len(target_room.users) >= target_room.max_player_count:
        player_usernames = [user.username for user in target_room.users]

        socketio.emit(
            "start_game",
            {"players": player_usernames},
            room=room_id,
        )
        print("rejoin_waiting_room: Játék indul a szobában:", room_id)
        start_game(player_usernames, room_id)

    broadcast_room_list_update()
    db.close()


@socketio.on("rejoin_game")
def handle_rejoin_game(data: dict) -> None:
    username = data["username"]
    room_id = data["room_id"]
    print("Rejoin game request received for room:", room_id)

    target_room = ROOMS.get(room_id)
    if not target_room:
        return

    print(f"Szoba megtalálva: {target_room.name}, {target_room.room_id}")

    for user in target_room.users:
        user.current_room_id = target_room.room_id
        print(f"Játékos: {user.username, user.current_room_id, user.is_active}")

    if room_id in game_instances:
        for player in game_instances[room_id].state.players:
            print(f"Játékos a játékban: {player.name, player.is_active}")
            print(f"Játékos kártyái: {player.cards_in_hand}")
            print(f"Játékos kártyái elől: {player.cards_in_front}")

        jatekosok = [player.name for player in game_instances[room_id].state.players]
        aktiv_jatekos = game_instances[room_id].state.active_player.name

        for user in USERS.values():
            for player in game_instances[room_id].state.players:
                if user.username == player.name:
                    player.is_active = user.is_active

        aktual_game_state = {
            "room_id": target_room.room_id,
            "activ_users": [u.username for u in USERS.values() if u.is_active],
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
        for j in game_instances[room_id].state.players:
            player_data[j.name] = {
                "cards_in_front": j.cards_in_front,
                "card_count": len(j.cards_in_hand),
                "is_active": j.is_active,
            }

        for j in game_instances[room_id].state.players:
            player_sid = sockets.get(j.name)
            if player_sid:
                cards_in_hand = [k.name for k in j.cards_in_hand]
                emit(
                    "player_data",
                    {
                        "name": j.name,
                        "cards_in_hand": cards_in_hand,
                        "starting_player": game_instances[
                            room_id
                        ].state.active_player.name,
                        "player_data": player_data,
                    },
                    to=player_sid,
                )

        print("handle_rejoin_game: Játékos újracsatlakozott a szobához:", room_id)
        start_game(aktual_game_state["players"], target_room.room_id, True)


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

    target_room = ROOMS.get(room_id)
    if not target_room:
        return

    print(f"Szobanév: {target_room.name}")
    if not hasattr(target_room, "voters"):
        target_room.voters = []

    if username not in target_room.voters:
        target_room.voters.append(username)

    if len(target_room.voters) >= target_room.max_player_count:
        print(f"Új játék indul a szobában: {room_id}")
        print(f"szobák: {game_instances}")
        game_instance = game_instances[room_id]
        if game_instance.state.id not in target_room.game_ids:
            target_room.game_ids.append(game_instance.state.id)
        player_usernames = [user.username for user in target_room.users]
        socketio.emit(
            "start_game",
            {
                "message": "Új játék kezdődik!",
                "players": player_usernames,
                "room_id": room_id,
                "game_ids": target_room.game_ids,
            },
            room=room_id,
        )
        target_room.voters = []
        print("handle_vote_rematch: Játék újraindítása a szobában:", room_id)
        start_game(player_usernames, room_id)
    else:
        print(f"Szavazás érkezett a szobában: {room_id}")
        socketio.emit(
            "rematch_vote_received",
            {"voters": target_room.voters, "room_id": room_id},
            room=room_id,
        )


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

    existing_user = USERS.get(username)
    if existing_user and existing_user.is_active:
        emit("login_error", {"message": "Ez a felhasználó már be van jelentkezve."})
        db.close()
        return

    session["socket_id"] = request.sid
    sockets[username] = session["socket_id"]
    session["username"] = username
    previous_room_id = dbuser.current_room_id
    previous_room = ROOMS.get(previous_room_id) if previous_room_id else None

    if username not in USERS:
        USERS[username] = User(
            username=username,
            password=password,
            current_room_id=previous_room_id,
            is_active=True,
        )
    else:
        USERS[username].is_active = True
        USERS[username].current_room_id = previous_room_id

    rooms_data = get_rooms_data()
    emit("login_success", {"username": username, "rooms": rooms_data})

    if previous_room:
        rooms_data = {}
        for room in ROOMS.values():
            rooms_data[room.room_id] = {
                "name": room.name,
                "player_count": room.max_player_count,
                "password_protected": True if room.password else False,
                "actual_player_count": len([user for user in room.users if user]),
                "game_ids": room.game_ids,
            }
        user_in_room = any(user.username == username for user in previous_room.users)
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
            db.close()
            return
        else:
            dbuser.current_room_id = None
            USERS[username].current_room_id = None
            db.commit()

    db.close()


def get_rooms_data():
    rooms_data = {}
    for room_id, room in ROOMS.items():
        if room_id not in game_instances:
            rooms_data[room_id] = {
                "name": room.name,
                "player_count": room.max_player_count,
                "password_protected": True if room.password else False,
                "actual_player_count": len(room.users),
            }
    return rooms_data


def broadcast_room_list_update():
    rooms_data = get_rooms_data()
    for username, user in USERS.items():
        if username in sockets and not user.current_room_id:
            socketio.emit("rooms_updated", {"rooms": rooms_data}, to=sockets[username])


@socketio.on("logout")
def handle_logout(data) -> None:
    print("Kliens kijelentkezett")
    username = data["username"]
    if not username:
        return

    user = USERS.get(username)
    if user:
        user.is_active = False
        syncronise_user_db(user)

    sockets.pop(username, None)

    if user and user.current_room_id:
        room = ROOMS.get(user.current_room_id)
        if room:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in room.users],
                    "activ_users": [u.username for u in USERS.values() if u.is_active],
                    "max_player_count": room.max_player_count,
                },
                room=user.current_room_id,
            )

    session.pop("username", None)


@socketio.on("disconnect")
def handle_disconnect() -> None:
    print("Kliens lecsatlakozott")
    username = session.get("username")
    if not username:
        return

    user = USERS.get(username)
    if user:
        user.is_active = False
        syncronise_user_db(user)

    sockets.pop(username, None)

    if user and user.current_room_id:
        room = ROOMS.get(user.current_room_id)
        if room:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in room.users],
                    "activ_users": [u.username for u in USERS.values() if u.is_active],
                    "max_player_count": room.max_player_count,
                },
                room=user.current_room_id,
            )


def remove_all_users_from_room(room_id: str) -> None:
    db: Session = get_db_session()
    print(f"Removing all users from room {room_id}")

    target_room = ROOMS.get(room_id)
    if not target_room:
        db.close()
        return

    users_to_remove = list(target_room.users)
    socketio.emit("left_room", {"message": "Szoba elhagyás"}, room=room_id)

    for user in users_to_remove:
        username = user.username
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if db_user:
            db_user.current_room_id = None

        user.current_room_id = None
        leave_room(room_id)
        target_room.users.remove(user)

    db.commit()

    if not target_room.users:
        del ROOMS[room_id]

    broadcast_room_list_update()
    db.close()


@socketio.on("leave_room")
def handle_leave_room(data: dict) -> None:
    """
    Handle user leaving a room
    """
    db: Session = get_db_session()
    print(f"LEAVE ROOM{data['username']}")
    username = session.get("username")

    user = USERS.get(username)
    if not user:
        db.close()
        return

    room_id = user.current_room_id
    target_room = ROOMS.get(room_id)

    if not target_room:
        db.close()
        return
    if ROOMS[room_id].game_ids != [] and room_id in game_instances:
        if game_instances[room_id].state.game_status == "run":
            remove_all_users_from_room(room_id)

    if user in target_room.users:
        target_room.users.remove(user)
        user.current_room_id = None

        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if db_user:
            db_user.current_room_id = None
        db.commit()

        leave_room(room_id)
        emit("left_room", {"message": "Szoba elhagyás"})

        if target_room.users:
            socketio.emit(
                "player_left_room",
                {
                    "message": f"{username} elhagyta a szobát",
                    "left_player": username,
                    "players": [u.username for u in target_room.users],
                    "activ_users": [u.username for u in USERS.values() if u.is_active],
                    "max_player_count": target_room.max_player_count,
                },
                room=room_id,
            )
        else:
            del ROOMS[room_id]

    syncronise_room_db(target_room)
    broadcast_room_list_update()
    db.close()


@socketio.on("create_room")
def create_room(data: dict) -> None:
    db: Session = get_db_session()
    username = session.get("username")

    room_id: str = str(uuid.uuid4())

    room = Room(
        room_id=room_id,
        name=data["room_name"],
        max_player_count=data["max_player_count"],
    )

    password = None
    if data["password_protected"]:
        password = data["password"]
        room.password = password

    ROOMS[room_id] = room
    syncronise_room_db(room)

    join_user_to_room(room_id, username, skip_password_check=True)
    broadcast_room_list_update()
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
    room = ROOMS.get(room_id)
    if not room:
        return False

    if not room.password:
        return True

    return room.password == provided_password


def join_user_to_room(
    room_id: str, username: str, skip_password_check: bool = False
) -> None:
    db: Session = get_db_session()

    user = USERS.get(username)
    target_room = ROOMS.get(room_id)

    if not user or not target_room:
        db.close()
        return

    if user not in target_room.users:
        target_room.users.append(user)
    user.current_room_id = room_id

    join_room(room_id)

    db_user = db.query(DBUser).filter(DBUser.username == username).first()
    if db_user:
        db_user.current_room_id = room_id
    db.commit()

    syncronise_room_db(target_room)
    room_joined()
    broadcast_room_list_update()

    socketio.emit(
        "room_players_updated",
        {
            "room_id": room_id,
            "players": [u.username for u in target_room.users],
            "activ_users": [u.username for u in USERS.values() if u.is_active],
            "max_player_count": target_room.max_player_count,
        },
        room=room_id,
    )

    if len(target_room.users) >= target_room.max_player_count:
        player_usernames = [user.username for user in target_room.users]

        socketio.emit(
            "start_game",
            {"players": player_usernames},
            room=room_id,
        )
        print("join_user_to_room: Játék indul a szobában:", room_id)
        start_game(player_usernames, room_id)
        broadcast_room_list_update()

    db.close()


def room_joined() -> None:
    db: Session = get_db_session()
    username = session.get("username")

    user = USERS.get(username)
    if not user:
        db.close()
        return

    current_room = ROOMS.get(user.current_room_id)
    if not current_room:
        db.close()
        return

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
    db.close()


def get_user_room_id(username: str) -> Optional[str]:
    user = USERS.get(username)
    return user.current_room_id if user else None


def get_game_instance(room_id: str) -> Optional[GameLogic]:
    return game_instances.get(room_id)


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid
    username = session.get("username")
    room_id = get_user_room_id(username)

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

    for j in game_instance.state.players:
        player_sid = sockets.get(j.name)
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

    db.close()


def card_content(room_id: str):
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


def place_card(room_id: str) -> None:
    game_instance = get_game_instance(room_id)

    for username, user in USERS.items():
        for player in game_instance.state.players:
            if user.username == player.name:
                player.is_active = user.is_active

    player_data = {}
    for j in game_instance.state.players:
        print(j.cards_in_front)
        player_data[j.name] = {
            "cards_in_front": j.cards_in_front,
            "card_count": len(j.cards_in_hand),
            "is_active": j.is_active,
        }

    print("player_data:")
    print(player_data)

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
        game_end(room_id)


def game_end(room_id: str) -> None:
    db = get_db_session()
    room = db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

    game = (
        db.query(Game)
        .filter(
            Game.id == game_instances[room_id].state.id,
            Game.loser_username == None,
        )
        .order_by(Game.id.desc())
        .first()
    )

    game_instance = get_game_instance(room_id)
    game_instance.state.loser_username = game_instance.state.active_player.name
    game_instance.state.game_status = "end"
    if game and game_instance:
        game.loser_username = game_instance.state.loser_username
        game.game_status = game_instance.state.game_status
        db.commit()

        socketio.emit(
            "game_over",
            {
                "losing_player": game_instance.state.active_player.name,
            },
            room=room_id,
        )

    db.close()


def start_game(players: list, room_id: str, reconnect: bool = False) -> None:
    global game_instances
    db = get_db_session()
    if reconnect:
        print("RECONNECT JÁTÉK INDÍTÁSA")
        if room_id in game_instances:
            game_instance = game_instances[room_id]
            print(f"Reconnecting to existing game in room {room_id}")

            for username, user in USERS.items():
                for player in game_instance.state.players:
                    if user.username == player.name:
                        player.is_active = user.is_active

            active_name = game_instance.state.active_player.name
            player_data = {}
            for j in game_instance.state.players:
                print("card_in_front:")
                print(j.cards_in_front)
                player_data[j.name] = {
                    "cards_in_front": j.cards_in_front,
                    "card_count": len(j.cards_in_hand),
                    "is_active": j.is_active,
                }

            for j in game_instance.state.players:
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
                    player_sid = sockets.get(j.name)
                    if (
                        player_sid
                        and j.name in game_instance.state.question_card.visited_already
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

            db.close()
            return
    else:
        print("ÚJ JÁTÉK INDUL")
        unique_game_id = str(uuid.uuid4())

        print(f"Egyedi játék ID: {unique_game_id}")

        game_instances[room_id] = GameLogic(
            unique_game_id, [Player(str(user)) for user in players]
        )
        print("Játék példány létrehozva:", game_instances[room_id])
        game_instance = game_instances[room_id]
        print("JÁTÉKID:", game_instance.state.id)

        if game_instance.state.id not in ROOMS[room_id].game_ids:
            ROOMS[room_id].game_ids.append(game_instance.state.id)
        print("Szoba játék ID-k:", ROOMS[room_id].game_ids)
        game = Game(id=game_instance.state.id, loser_username=None)
        db.add(game)

        db_room = db.query(DBRoom).filter_by(room_id=room_id).first()
        if game not in db_room.game_ids:
            db_room.game_ids.append(game)

        db.commit()
        print(f"Új játék létrehozva és hozzárendelve a szobához: {game.id} → {room_id}")

        active_name = game_instance.state.active_player.name
        for username, user in USERS.items():
            for player in game_instance.state.players:
                if user.username == player.name:
                    player.is_active = user.is_active

        player_data = {}
        for j in game_instance.state.players:
            player_data[j.name] = {
                "cards_in_front": j.cards_in_front,
                "card_count": len(j.cards_in_hand),
                "is_active": j.is_active,
            }
            print("kartyak szama", len(j.cards_in_hand))

        for j in game_instance.state.players:
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

        db.close()


if __name__ == "__main__":
    reset_database()
    socketio.run(app, debug=True, host="0.0.0.0")
