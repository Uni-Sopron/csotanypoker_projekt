import socket
import threading
import json
import random
import string
import time
from  csotanypoker.server.game import jatek, jatekos
#TODO : Jelszó titkositás
#TODO: JELSZÓ ellenörzése
# TODO: Felhasználoi interakciók hibák kezelése
# egyedi szobanevek





class Room:
    def __init__(self, name, password="", max_players=2, random=False):
        self.name = name
        self.password = password
        self.max_players = max_players
        self.players = []
        self.random= random
    
    def jatekos_hozzaadas(self, player):
        if len(self.players) < self.max_players :
            self.players.append(player)
            return True
        return False

class Server:
    def __init__(self, host="127.0.0.1", port=55555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        self.clients = []
        self.rooms = {}

    def handle_client(self, client, addr):
        client.send((json.dumps({"type": "Szerver_csatlakozas", "message": "Csatlakozás a szerverehez!\n"}) ).encode("ascii"))
        while True:
            try:
                data = client.recv(1024).decode("ascii")
                message = json.loads(data)
                self.handle_message(client, message,addr)
            except:
                break
        client.close()

    def handle_message(self, client, message, addr):
        message_type = message.get("type")

        if message_type == "nev":
            player = jatekos(message.get("nev"), client, addr)
            self.clients.append(player)
            print(f"Kapcsolódott: {player.nev}")
            
        elif message_type == "create_room":
            for player in self.clients:
                if player.client == client:
                    self.create_room(player, message)
                    print("Szoba létrehozva")

        elif message_type == "join_room":
            for player in self.clients:
                if player.client == client:
                    self.join_room(player, message.get("room_name"), message.get("password"))
                    print("Szobához csatlakozva")

        elif message_type == "get_rooms":  
            room_list = []
            for room in self.rooms.values():
                if len(room.players) < room.max_players and not room.random:
                    room_list.append(room.name)
            
            client.send((json.dumps({"type": "szoba nevek", "rooms": room_list}) ).encode("ascii"))
            print(f"Szobák listája elküldve: {room_list}")
        elif message_type == "random_room":
            for player in self.clients:
                if player.client == client:
                    self.random_room(player)
                    print("Véletlenszerű szobához csatlakozva")
    
    
    
    def create_room(self, player, message):
        room_name = message.get("room_name")
        password = message.get("password")
        max_players = message.get("max_players", 2)  
        room = Room(room_name, password, max_players)
        self.rooms[room_name] = room
        room.jatekos_hozzaadas(player)
        player.client.send((json.dumps({"type": "Varakozas", "message": "Várakozunk a játékosokra"}) ).encode("ascii"))
        self.start_game(room)


    def join_room(self, client, room_name, password):
        room = self.rooms.get(room_name)
        if room and room.password == password :
            room.jatekos_hozzaadas(client)
            client.client.send((json.dumps({"type": "Varakozas", "message": "Varakozunk a játékosokra"}) ).encode("ascii"))
            self.start_game(room)
        

    def random_room(self, player):
        for room in self.rooms.values():
            if room.random and len(room.players) < room.max_players:
                room.jatekos_hozzaadas(player)
                player.client.send((json.dumps({"type": "Varakozas", "message": "Várakozunk a játékosokra"}) ).encode("ascii"))
                self.start_game(room)
                return
        
        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=5)) # véletlen szeru szoba nev
        new_room = Room(random_name, random=True)
        self.rooms[random_name] = new_room
        new_room.jatekos_hozzaadas(player)
        player.client.send((json.dumps({"type": "Varakozas", "message": "Várakozunk a játékosokra"})).encode("ascii"))
        
    def start_game(self, room):
        if len(room.players) == room.max_players:
            jatek_inditas=jatek(room.players)
            print(f"Elindult a játék {room.name} szobában...")
            for player in room.players:
                kartyak = [kartya.nev for kartya in player.kezbenlevo_kartyak]
               
                player.client.send((json.dumps({
                    "type": "game_start",
                    "message": "Game starting...",
                    "lapok": kartyak
                }) ).encode("ascii"))
        else :
            for player in room.players:
                player.client.send((json.dumps({"type": "Varakozas", "message": "Várunk a játékosokra..."})).encode("ascii"))

    
    
    def start(self):
        print("Szerver elindult.")
        while True:
            client, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(client, addr)).start()


if __name__ == "__main__":
    server = Server()
    server.start()