from typing import Optional


class User:
    def __init__(
        self,
        username: str,
        password: Optional[str] = None,
        current_room_id: Optional[str] = None,
        is_active: bool = True,
    ):
        self._username: str = username
        self._password: Optional[str] = password
        self._current_room_id: Optional[str] = current_room_id
        self._is_active: bool = is_active

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        self._username = value

    @property
    def password(self) -> Optional[str]:
        return self._password

    @password.setter
    def password(self, value: Optional[str]) -> None:
        self._password = value

    @property
    def current_room_id(self) -> Optional[str]:
        return self._current_room_id

    @current_room_id.setter
    def current_room_id(self, value: Optional[str]) -> None:
        self._current_room_id = value

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._is_active = value