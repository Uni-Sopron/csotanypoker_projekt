from ast import List

from pyparsing import Optional


class Room:
    def __init__(
        self,
        room_id: str,
        name: str,
        max_player_count: int = 4,
    ):
        self.room_id: str = room_id
        self.name: str = name
        self.game_ids: List[
            str
        ] = []  # ha ez üres akkor még nincs játék inditva tehát meg kell jeleniteni a szobát a szoba lista oldalon ha nem üres akkor nem kell megjeleniteni
        
        self.max_player_count: int = max_player_count  # adatbazisba
        self.password_protected: bool = False
        self.password: Optional[str] = None
        self.users: List[str] = []
        self.player_count: int = 0
        

    def __repr__(self):
        return f"Room(room_id={self.room_id}, name={self.name}, player_count={self.player_count})"
