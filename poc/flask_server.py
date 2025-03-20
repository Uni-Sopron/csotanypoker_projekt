from flask import Flask, request
from flask_socketio import SocketIO, send

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  

clients = {}  

@app.route("/")
def index():
    return "szerver fut!"

@socketio.on("connect")
def handle_connect():
    print("Új felhasználó csatlakozott!")

@socketio.on("register")
def handle_register(username):
    clients[getattr(request, "sid")] = username
    send(f"{username} csatlakozott a csevegéshez!", broadcast=True)

@socketio.on("message")
def handle_message(message):
    username = clients.get(getattr(request, "sid"), "Ismeretlen")
    send(f"{username}: {message}", broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    username = clients.pop(getattr(request, "sid"), "Ismeretlen")
    send(f"{username} kilépett a csevegésből.", broadcast=True)
    print(f"{username} kilépett.")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5555, debug=True)
