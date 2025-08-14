import socket
import select
from typing import Dict, Tuple, Union, Optional


class ChatServer:
    def __init__(self, host: str = "localhost", port: int = 5555) -> None:
        """
        Args:
            host (str): Server IP address. Defaults to 'localhost'.
            port (int): Server port number. Defaults to 5555.
        """
        self.host: str = host
        self.port: int = port

        # Create server socket
        self.server_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )  # ipv4 and tcp
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  # The system reuses addresses for faster restarts.

        self.clients: Dict[socket.socket, Dict[str, Union[str, bool, None]]] = {}
        self.running: bool = False

    def start_server(self) -> None:
        """
        Start the server and handle client connections and messages.
        """

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()  # 5 clients can connect at the same time
        self.running = True

        print(f"Server running on {self.host}:{self.port}")

        while self.running:
            # Select monitors the server socket and all client sockets to see which one is receiving data. This way you don't have to start a separate thread for each client.
            read_sockets, _, _ = select.select(
                [self.server_socket] + list(self.clients.keys()), [], []
            )

            for sock in read_sockets:
                if sock == self.server_socket:  # New connection
                    client_socket, client_address = self.server_socket.accept()
                    self.handle_new_connection(client_socket, client_address)
                else:  # Existing client message
                    self.handle_client_message(sock)

    def handle_new_connection(
        self, client_socket: socket.socket, address: Tuple[str, int]
    ) -> None:
        """
        Handle a new client connection.

        Args:
            client_socket (socket.socket): Socket for the new client.
            address (Tuple[str, int]): Client's network address.
        """
        self.clients[client_socket] = {"username": None}
        client_socket.send("Please enter your name: ".encode())
        print(f"Új kapcsolat: {address}")

    def handle_client_message(self, client_socket: socket.socket) -> None:
        """
        Handles the messages sent by the client.
        Args:
            client_socket(socket.socket): The client's socket.
        """
        try:
            message = (
                client_socket.recv(1024).decode().strip()
            )  # Receiving messages with a max size of 1024 bytes
            if message == "exit":  # Client exit
                self.remove_client(client_socket)
                return
            if (
                self.clients[client_socket]["username"] is None
            ):  # If the client is not registered (first message is their username)
                if any(
                    client["username"] == message for client in self.clients.values()
                ):
                    client_socket.send(
                        "Válassz másik nevet ez a név foglalt. ".encode()
                    )
                else:
                    self.clients[client_socket] = {"username": message}
                    welcome_msg = f"{message} csatlakozott a beszélgetéshez!"
                    self.broadcast(welcome_msg, client_socket)
            else:
                # Sending a normal message
                username = self.clients[client_socket]["username"]
                self.broadcast(f"{username}: {message}", client_socket)

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            self.remove_client(client_socket)
            print(f"Hiba: {e}")

    def broadcast(self, message: str, sender_socket: Optional[socket.socket]) -> None:
        """
        Send a message to all connected clients except the sender.

        Args:
            message (str): The message to send
            sender_socket (socket.socket): The sender's socket
        """
        for client_socket in self.clients.keys():
            if (
                client_socket != sender_socket
                and self.clients[client_socket]["username"] is not None
            ):
                try:
                    client_socket.send(message.encode())
                except (
                    ConnectionResetError,
                    ConnectionAbortedError,
                    BrokenPipeError,
                ) as e:
                    self.remove_client(client_socket)
                    print(f"Hiba: {e}")

    def remove_client(self, client_socket: socket.socket) -> None:
        """
        Remove a client from the server.

        Args:
            client_socket (socket.socket): The socket of the client to remove
        """
        if client_socket in self.clients:
            username = self.clients[client_socket]["username"]
            print(f"{username} kilépett.")
            del self.clients[client_socket]

            self.broadcast(f"{username} kilépett.", None)
            try:
                client_socket.close()
            except OSError:
                pass


if __name__ == "__main__":
    server = ChatServer()
    server.start_server()
