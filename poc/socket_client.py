import socket
import threading

class ChatClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def connect(self):
        self.socket.connect((self.host, self.port))
        self.running = True
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_loop()

    def receive_messages(self):
        while self.running:
            try:
                message = self.socket.recv(1024).decode()
                if message:
                    print(message)
            except InterruptedError:
                break

    def send_loop(self):
        while self.running:
            message = input()
            if message.lower() == 'exit':
                self.socket.close()
                self.running = False
                break
            self.socket.send(message.encode())

if __name__ == "__main__":
    client = ChatClient()
    client.connect()
