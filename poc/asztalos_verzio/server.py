from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid


from adatbazis import User, Room, get_db_session


app = Flask(__name__)
socketio = SocketIO(
    app, cors_allowed_origins="*"
)  # cors_allowed_origins="*" -> Allow access for everyone.


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("login")
def handle_login(data):
    username = data["username"]
    session["username"] = username

    db = get_db_session()
    user = db.query(User).filter(User.username == username).first()

    if (
        not user
    ):  # If there is no such user, create it; if it exists, update the socket_id.
        user = User(username=username, socket_id=getattr(request, "sid"))
        db.add(user)
    else:
        user.socket_id = getattr(request, "sid")

    db.commit()
    db.close()

    emit(
        "login_success", {"username": username}
    )  # We send the username back to the client.


@socketio.on("get_rooms")
def handle_get_rooms():
    db = get_db_session()
    room_list = []
    rooms = db.query(Room).all()

    for room in rooms:
        print(room.game_started)
        if room.game_started == False:
            room_list.append(
                {
                    "id": room.room_id,
                    "name": room.name,
                    "players": len(room.players),
                    "max_players": room.player_count,
                }
            )

    db.close()
    emit("room_list", {"rooms": room_list})


@socketio.on("create_room")
def handle_create_room(data):
    room_id = str(uuid.uuid4())
    room_name = data["name"]
    palyer_count = 3
    db = get_db_session()
    new_room = Room(room_id=room_id, name=room_name, player_count=palyer_count)
    db.add(new_room)
    db.commit()
    db.close()

    emit("room_created", {"id": room_id, "name": room_name}, broadcast=True)


@socketio.on("join_room")
def handle_join_room(data):  # If the user enters a room.
    room_id = data["room_id"]
    username = session["username"]

    db = get_db_session()  # We fetch the data from the database.
    room = db.query(Room).filter(Room.room_id == room_id).first()
    user = db.query(User).filter(User.username == username).first()

    if user:
        user.current_room_id = room_id
        db.commit()

    join_room(room_id)  # We let the user into the room.
    # Ellenőrizzük, hogy a szoba létezik-e
    if not room:
        emit("error", {"message": "A szoba nem található"})
        db.close()
        return
    player_names = [player.username for player in room.players]
    emit(  # It only sends the message to the one who triggered this event, i.e., the connecting player.
        "joined_room",
        {
            "room_id": room_id,
            "name": room.name,
            "players": player_names,
        },
    )

    emit(  # We send this to the other players in that room.
        "player_joined",
        {
            "players": player_names,
        },
        room=room_id,
    )  # room=room_id means that we only send it to the players in that specific room (this can be used because of join_room).

    if len(room.players) == room.player_count:
        room.game_started = True
        room.set_game_started(True)
        db.commit()
        emit("start_game", {"players": player_names}, room=room_id)

    db.close()


@socketio.on("leave_room")  # If the user exits the room.
def handle_leave_room(data):
    room_id = data["room_id"]
    username = session["username"]

    db = get_db_session()
    room = db.query(Room).filter(Room.room_id == room_id).first()
    user = db.query(User).filter(User.username == username).first()
    if user:
        if user.current_room_id == room_id:
            # user.current_room_id = None
            user.set_current_room_id(None)

            db.commit()
    leave_room_helper(room_id, username, room, db)
    db.close()


def leave_room_helper(room_id, username, room, db):
    leave_room(room_id)
    player_names = [player.username for player in room.players]
    emit(
        "player_left",
        {
            "players": player_names,
        },
        room=room_id,
    )

    emit(
        "user_notification",
        {"message": f"{username} has left the room."},
        room=room_id,
    )

    if not room.players:
        db.delete(room)
        db.commit()
        emit("room_closed", {"room_id": room_id}, broadcast=True)


@socketio.on("player_click")
def handle_player_click(data):
    clicked_player = data["clicked_player"]
    clicking_player = session["username"]

    db = get_db_session()
    target_user = db.query(User).filter(User.username == clicked_player).first()

    if target_user is not None and target_user.socket_id is not None:
        emit(  # We only send the message to the targeted player.
            "user_notification",
            {"message": f"{clicking_player} clicked on you."},
            to=str(target_user.socket_id),
        )

    db.close()


@socketio.on("disconnect")
def handle_disconnect():
    username = session.get("username")

    db = get_db_session()
    user = db.query(User).filter(User.username == username).first()

    if user is not None and user.current_room_id is not None:
        room_id = user.current_room_id
        room = db.query(Room).filter(Room.room_id == room_id).first()

        if room:
            user.current_room_id = None
            db.commit()

            leave_room_helper(room_id, username, room, db)

    db.close()


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0")
