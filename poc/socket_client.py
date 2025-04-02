import socket
import threading


class ChatClient:
    def __init__(self, host: str = "localhost", port: int = 5555) -> None:
        """
        Args:
            host (str): The server's IP address. Default is "localhost".
            port (int): The port on which the server is running. Default is 5555.
        """
        self.host: str = host
        self.port: int = port
        self.socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )  # ipv4 and tcp
        self.running: bool = False

    def connect(self) -> None:
        """
        Connect to the server and start the message-handling thread.
        """
        self.socket.connect((self.host, self.port))
        self.running: bool = True
        threading.Thread(
            target=self.receive_messages, daemon=True
        ).start()  # message-receiving thread
        self.send_loop()

    def receive_messages(self) -> None:
        """
        Continuously receives messages from the server and displays them on the console.
        """
        while self.running:
            try:
                message = (
                    self.socket.recv(1024).decode()
                )  # receive messages from the server with a max length of 1024 bytes
                if message:
                    print(message)
            except socket.error:
                break

    def send_loop(self) -> None:
        """
        Prompts the user for a message and sends it to the server.
        If the message is "exit", it will terminate the connection.
        """
        while self.running:
            try:
                message = input()
                self.socket.send(message.encode())  # send message to the server
                if message.lower() == "exit":  # exit
                    self.running = False
                    break
                if (
                    "Válassz másik nevet ez a név foglalt" in message
                ):  # if the name is already taken
                    print(message)
                    continue
            except KeyboardInterrupt:
                message = "exit"
                self.socket.send(message.encode())
                self.running = False
                break


if __name__ == "__main__":
    client = ChatClient()
    client.connect()
