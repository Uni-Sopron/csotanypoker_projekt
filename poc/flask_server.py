from flask import Flask, request
from flask_socketio import SocketIO, send

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {}


@socketio.on("connect")
def handle_connect() -> None:
    """
    When a new client connects, it displays that a new user has joined.
    """
    print("Új felhasználó csatlakozott!")


@socketio.on("register")
def handle_register(username: str) -> None:
    """
    Registers the user for the chat.
    If the name is already taken, it asks the user for a new name.
    Args:
        username (str): The user's name.
    """
    sid: str = getattr(request, "sid")
    if username in clients.values():
        socketio.emit("register_response", False, to=sid)
        print(f"{username} már foglalt név!")
    else:
        clients[sid] = username
        print(f"{username} csatlakozott a csevegéshez!")
        socketio.emit("register_response", True, to=sid)  # Username accepted
        for client_sid in clients.keys():
            send(f"{username} csatlakozott a csevegéshez!", to=client_sid)


@socketio.on("message")
def handle_message(message: str) -> None:
    """
    Receives a user's message and forwards it to the other users.
    Args:
        message (str): The user's message."""
    sid: str = getattr(request, "sid")

    if sid not in clients:
        return

    username = clients[sid]
    for client_sid in clients.keys():
        send(f"{username}: {message}", to=client_sid)


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """
    Removes the exited user from the chat and notifies the other users about it.
    """
    username: str = clients.pop(getattr(request, "sid"))
    for client_sid in clients.keys():
        send(f"{username} kilépett a csevegésből.", to=client_sid)
    print(f"{username} kilépett.")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5555, debug=True)
