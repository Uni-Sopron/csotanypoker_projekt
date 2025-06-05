class Room:
    def __init__(
        self,
        room_id: str,
        name: str,
        game_started: bool = False,
        max_player_count: int = 4,
    ):
        self.room_id = room_id
        self.name = name
        self.game_started = game_started
        self.max_player_count = max_player_count
        self.password_protected = False
        self.password = None
        self.users = []
        self.player_count = 0

    def __repr__(self):
        return f"Room(room_id={self.room_id}, name={self.name}, game_started={self.game_started}, player_count={self.player_count})"
