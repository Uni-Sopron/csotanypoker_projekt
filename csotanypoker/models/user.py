from typing import Optional


class User:
    def __init__(
        self,
        username: str,
        password: Optional[str] = None,
        current_room_id: Optional[str] = None,
        is_active: bool = True,
    ):
        self.username = username
        self.password = password
        self.current_room_id = current_room_id
        self.is_active = is_active
        self.current_room = None
        self.player = None
