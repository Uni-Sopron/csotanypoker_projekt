import logging
import socket
import select

class ChatServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  
        self.running = False

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
    
        print(f"Szerver fut: {self.host}:{self.port}")

        while self.running:
            read_sockets, _, _ = select.select([self.server_socket] + list(self.clients.keys()), [], [])

            for sock in read_sockets:
                if sock == self.server_socket: 
                    client_socket, client_address = self.server_socket.accept()
                    self.handle_new_connection(client_socket, client_address)
                else:
                    self.handle_client_message(sock)

    def handle_new_connection(self, client_socket, address):
        self.clients[client_socket] = {'username': None, 'registered': False}
        client_socket.send("Kérlek, add meg a nevedet: ".encode())
        print(f"Új kapcsolat: {address}")

    def handle_client_message(self, client_socket):
        try:
            message = client_socket.recv(1024).decode().strip()
            if not message:
                self.remove_client(client_socket)
                return
            
            client_info = self.clients[client_socket]
            
            if not client_info['registered']:  
                self.clients[client_socket] = {'username': message, 'registered': True}
                welcome_msg = f"{message} csatlakozott a beszélgetéshez!"
                self.broadcast(welcome_msg, client_socket)
                print(welcome_msg)
            else:
                username = client_info['username']
                self.broadcast(f"{username}: {message}", client_socket)
                print(f"{username}: {message}")

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            self.remove_client(client_socket)
            logging.error(f"Hiba: {e}")

    def broadcast(self, message, sender_socket):
        for client_socket in self.clients.keys():
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode())
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
          
                    self.remove_client(client_socket)
                    logging.error(f"Hiba: {e}")

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            username = self.clients[client_socket]['username']
            print(f"{username} kilépett.")
            self.broadcast(f"{username} kilépett.", client_socket)
            del self.clients[client_socket]
            client_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start_server()
