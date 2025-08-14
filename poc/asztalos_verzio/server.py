from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from adatbazis import User, Room, get_db_session

app = Flask(__name__)  # Create Flask application
socketio = SocketIO(
    app, cors_allowed_origins="*"
)  # Create SocketIO server, allowing CORS from all origins


@socketio.on("connect")
def handle_connect() -> None:
    """
    When a new client connects, print that a new user has joined.
    """
    print("Kliens csatlakozott")


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
    # Check if the username is already in use
    if (
        user
        and user.is_active
        and user.socket_id
        and user.socket_id != getattr(request, "sid")
    ):
        emit(
            "login_error",
            {"message": "Ez a felhasználónév már foglalt."},
        )
        db.close()
        return

    session["username"] = username  # Store username in session

    if not user:  # If the user does not exist, create a new one
        db.add(
            User(username=username, socket_id=getattr(request, "sid"), is_active=True)
        )
    else:
        user.socket_id = getattr(request, "sid")
        user.set_active(True)  # Mark user as active

        # Check if the user was in an ongoing game
        if user.current_room_id:
            room = db.query(Room).filter(Room.room_id == user.current_room_id).first()
            if room and room.game_started:
                emit("rejoin_prompt", {"room_id": room.room_id, "room_name": room.name})
                db.commit()
                db.close()
                return

    db.commit()
    db.close()

    emit(
        "login_success", {"username": username, "screen_state": None}
    )  # Send the username back to the client


@socketio.on("get_rooms")
def handle_get_rooms() -> None:
    """
    Fetch all rooms that have not yet started
    and send them to the client.
    """
    db: Session = get_db_session()
    room_list: list = []
    rooms: list = db.query(Room).all()

    # Filter out already started games and only send rooms that are not running
    for room in rooms:
        print(room.game_started)
        if not room.game_started:
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
def handle_create_room(data: dict) -> None:
    """
    Creates a new room in the database and automatically adds
    the creator to the room.

    Args:
        data (dict): Dictionary containing the room name.
    """
    room_id: str = str(uuid.uuid4())  # Generate unique ID for the room
    room_name: str = data["name"]
    username: str = session["username"]

    db: Session = get_db_session()
    db.add(Room(room_id=room_id, name=room_name))

    user: User = (
        db.query(User).filter(User.username == username).first()
    )  # Add the creator to the room
    if user:
        user.current_room_id = room_id
        db.commit()

    db.close()

    emit("room_created", {"id": room_id, "name": room_name}, broadcast=True)

    join_room(room_id)

    # Fetch player list
    db: Session = get_db_session()
    room: Room = db.query(Room).filter(Room.room_id == room_id).first()
    player_names: list = [player.username for player in room.players] if room else []
    db.close()

    # Send new room details to the joining player
    emit(
        "joined_room",
        {
            "room_id": room_id,
            "name": room_name,
            "players": player_names,
            "username": username,
        },
    )


@socketio.on("join_room")
def handle_join_room(data: dict ) -> None:
    """
    Adds the user to the specified room and notifies the other
    players about the new joiner. If the room is full, starts the game.

    Args:
        data (dict): A dictionary containing the room ID.
    """
    room_id: str = data["room_id"]
    username: str = session["username"]
    rejoin: bool = data["rejoin"]
    db: Session = get_db_session()  # Retrieve data from the database
    room: Room = db.query(Room).filter(Room.room_id == room_id).first()
    user: User = db.query(User).filter(User.username == username).first()

    if user:
        user.current_room_id = room_id
        db.commit()

    join_room(room_id)
    if not room:
        emit("error", {"message": "A szoba nem található"})
        db.close()
        return
    player_names: list = [
        player.username for player in room.players if room and player.is_active
    ]

    # Send only to the joining player
    emit(
        "joined_room",
        {
            "room_id": room_id,
            "name": room.name,
            "players": player_names,
            "username": username,
        },
    )

    # Notify the other players that a new player has joined
    emit(
        "player_joined",
        {
            "players": player_names,
            "joined_player": username,
        },
        room=room_id,
    )

    # If the room is full, start the game
    if rejoin is False:
        if len(room.players) == room.player_count:
            room.game_started = True
            room.set_game_started(True)
            db.commit()
            emit("start_game", {"players": player_names}, room=room_id)
    else:
        emit("start_game", {"players": player_names}, room=room_id)
    db.close()


@socketio.on("leave_room")
def handle_leave_room(data: dict) -> None:
    """
    Removes the user from the specified room and notifies the other
    players about the player's departure. If the room is empty, deletes it from the database.

    Args:
        data (dict): A dictionary containing the room ID.
    """
    room_id: str = data["room_id"]
    username: str = session["username"]

    db: Session = get_db_session()
    room: Room = db.query(Room).filter(Room.room_id == room_id).first()
    user: Room = db.query(User).filter(User.username == username).first()
    if user:
        if user.current_room_id == room_id:
            user.set_current_room_id("")
            db.commit()

    leave_room_helper(room_id, username, room, db)
    db.close()


def leave_room_helper(room_id: str, username: str, room: Room, db) -> None:
    """
    This function notifies other players about a player's departure
    and deletes the room if it's empty.

    Args:
        room_id (str): The room ID.
        username (str): The name of the leaving user.
        room (Room): The room object.
        db: The database session.
    """
    leave_room(room_id)
    player_names = [player.username for player in room.players]

    # Notify other players that someone has left
    emit(
        "player_left",
        {
            "players": player_names,
            "left_player": username,
        },
        room=room_id,
    )

    # Send notification to players in the room
    emit(
        "user_notification",
        {"message": f"{username} kilépett."},
        room=room_id,
    )

    # If the room is empty, delete it
    if not room.players:
        db.delete(room)
        db.commit()
        emit("room_closed", {"room_id": room_id}, broadcast=True)


@socketio.on("player_click")
def handle_player_click(data: dict) -> None:
    """
    Handles when a player clicks on another player
    and sends a notification to the targeted player.

    Args:
        data (dict): Data received from the client, containing the target player's name.
    """
    clicked_player = data["clicked_player"]
    clicking_player = session["username"]

    db: Session = get_db_session()
    target_user: User = db.query(User).filter(User.username == clicked_player).first()

    if target_user is not None and target_user.socket_id is not None:
        # Notify the targeted player who clicked on them
        emit(
            "user_notification",
            {"message": f"{clicking_player} katintott rád!"},
            to=str(target_user.socket_id),
        )

    db.close()


@socketio.on("rejoin_decision")
def handle_rejoin_decision(data: dict) -> None:
    """
    Handles the player's decision to rejoin.
    If the player wants to rejoin, they re-enter the room.
    If not, they are removed from the room.

    Args:
        data (dict): A dictionary containing the decision and the room ID.
    """
    decision: bool = data["decision"]
    room_id: str = data["room_id"]

    username: str = session["username"]

    if decision:  # The player wants to rejoin the game
        handle_join_room({"room_id": room_id, "rejoin":True})
    else:  # The player does not want to rejoin
        handle_leave_room({"room_id": room_id})

        emit(
            "login_success",
            {
                "username": username,
                "screen_state": "lobby",
            },
        )



@socketio.on("disconnect")
def handle_disconnect() -> None:
    """
    Handles client disconnection and saves data for future reconnection.
    """
    username: Optional[str] = session.get("username")
    if not username:
        return

    db: Session = get_db_session()
    user: User = db.query(User).filter(User.username == username).first()

    if user is not None:
        user.set_active(False)  # The user becomes inactive

        if user.current_room_id is not None:
            room_id: str = user.current_room_id
            room: Room = db.query(Room).filter(Room.room_id == room_id).first()
            if room:
                # Notify other players about the disconnection
                leave_room(room_id)
                player_names = [
                    player.username
                    for player in room.players
                    if player.username != username
                ]
                emit(
                    "player_left",
                    {
                        "players": player_names,
                        "left_player": username,
                    },
                    room=room_id,
                )

                emit(
                    "user_notification",
                    {"message": f"{username} kilépett."},
                    room=room_id,
                )

                # If the room is empty, delete it
                if not player_names:
                    db.delete(room)
                    db.commit()
                    emit("room_closed", {"room_id": room_id}, broadcast=True)

    db.commit()
    db.close()


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0")
