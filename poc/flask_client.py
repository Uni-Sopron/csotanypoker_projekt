import socketio

sio = socketio.Client()


@sio.event
def connect() -> None:
    """Connects to the server."""
    try:
        username = input("Add meg a neved: ")
        sio.emit("register", username)
    except (KeyboardInterrupt, EOFError):
        sio.disconnect()


@sio.event
def register_response(success: bool) -> None:
    """
    The server's response to the registration. If the name is taken, it asks for a new name.
    Args:
        success (bool): If the name is taken, it will be False, otherwise True.
    """
    try:
        if not success:
            print("A név már foglalt, próbálj meg egy másikat!")
            username = input("Addj meg egy másik nevet: ")
            sio.emit("register", username)
        else:
            print("Sikeres regisztráció!")
    except (KeyboardInterrupt, EOFError):
        sio.disconnect()


@sio.event
def message(data: str) -> None:
    """
    Receives the server's messages and prints them to the console.
    Args:
        data (str): The server's message.
    """
    print(data)


@sio.event
def disconnect() -> None:
    """
    Prints that the connection has been terminated with the server.
    """
    print("Kapcsolat bontva.")


def start_client() -> None:
    """
    Starts the client. Connects to the server, prompts the user for messages, and sends them to the server.
    On the "exit" command, the client disconnects from the server.
    """
    sio.connect("http://localhost:5555")

    while True:
        try:
            msg = input()
            if msg.lower() == "exit":
                sio.disconnect()
                break
            sio.send(msg)
        except (KeyboardInterrupt, EOFError):
            sio.disconnect()
            break


if __name__ == "__main__":
    start_client()
