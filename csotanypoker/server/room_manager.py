import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from csotanypoker.models.user import Client_User
from csotanypoker.models.room import Room
from csotanypoker.server.database import DBUser, DBRoom, DBGame


class RoomManager:
    def __init__(self, socketio, sockets: dict):
        self.socketio = socketio
        self.sockets = sockets

    def get_room_by_id(self, db: Session, room_id: str) -> Optional[DBRoom]:
        return db.query(DBRoom).filter(DBRoom.room_id == room_id).first()

    def get_room_users(self, db: Session, room_id: str) -> List[DBUser]:
        return db.query(DBUser).filter(DBUser.current_room_id == room_id).all()

    def update_room_player_count(self, db: Session, room_id: str) -> None:
        room = self.get_room_by_id(db, room_id)
        if room:
            user_count = (
                db.query(DBUser).filter(DBUser.current_room_id == room_id).count()
            )
            room.player_count = user_count
            db.commit()

    def validate_room_password(
        self, db: Session, room_id: str, provided_password: str
    ) -> bool:
        room = self.get_room_by_id(db, room_id)
        if not room:
            return False

        if not room.password:
            return True

        return room.password == provided_password

    def create_room(
        self,
        db: Session,
        room_name: str,
        max_player_count: int,
        password: Optional[str] = None,
    ) -> DBRoom:
        while True:
            room_id = uuid.uuid4().hex[:15]
            existing = self.get_room_by_id(db, room_id)
            if not existing:
                break

        db_room = DBRoom(
            room_id=room_id,
            name=room_name,
            max_player_count=max_player_count,
            password=password,
            password_protected=bool(password),
        )

        db.add(db_room)
        db.commit()
        return db_room

    def join_user_to_room(self, db: Session, room_id: str, username: str) -> bool:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        target_room = self.get_room_by_id(db, room_id)

        if not db_user or not target_room:
            return False

        db_user.current_room_id = room_id
        db.commit()
        self.update_room_player_count(db, room_id)
        return True

    def remove_user_from_room(self, db: Session, username: str) -> Optional[str]:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user or not db_user.current_room_id:
            return None

        room_id = db_user.current_room_id
        db_user.current_room_id = None
        db.commit()
        self.update_room_player_count(db, room_id)
        return room_id

    def remove_all_users_from_room(
        self,
        db: Session,
        room_id: str,
        current_username: Optional[str] = None,
        reconnecting: bool = False,
    ) -> List[str]:
        target_room = self.get_room_by_id(db, room_id)
        if not target_room:
            return []

        room_users = self.get_room_users(db, room_id)
        removed_users = []

        for user in room_users:
            dbuser = db.query(DBUser).filter(DBUser.username == user.username).first()

            if reconnecting and dbuser.username == current_username:
                dbuser.is_active = True
                db.commit()

            if dbuser:
                dbuser.current_room_id = None
                removed_users.append(user.username)

                if user.username in self.sockets:
                    try:
                        if dbuser.is_active or not dbuser.is_active:
                            self.socketio.emit(
                                "left_room",
                                {"message": "Szoba elhagyás"},
                                to=self.sockets[user.username],
                            )
                            dbuser.is_active = True
                            db.commit()
                    except Exception as e:
                        print(f"Error notifying user {user.username}: {e}")
                        self.sockets.pop(user.username, None)

        db.commit()
        self.update_room_player_count(db, room_id)
        self.broadcast_room_list_update(db)
        return removed_users

    def get_rooms_data(self, db: Session) -> dict:
        rooms_data = {}
        rooms = db.query(DBRoom).all()

        for room in rooms:
            player_count = self.user_counter(db, room.room_id)
            has_running_game = self.game_is_running(db, room.room_id)
            has_human = self.has_human_player_in_room(db, room.room_id)

            if not has_running_game and player_count != 0 and has_human:
                rooms_data[room.room_id] = {
                    "name": room.name,
                    "max_player_count": room.max_player_count,
                    "password_protected": True if room.password else False,
                    "player_count": player_count,
                }

        return rooms_data

    def user_counter(self, db: Session, room_id: str) -> int:
        users = self.get_room_users(db, room_id)
        return len(users)

    def game_is_running(self, db: Session, room_id: str) -> bool:
        running_game = (
            db.query(DBGame)
            .filter(DBGame.room_id == room_id, DBGame.game_status == "run")
            .first()
        )
        return running_game is not None

    def has_human_player_in_room(self, db: Session, room_id: str) -> bool:
        from csotanypoker.models.user import AI_NAMES

        room_users = self.get_room_users(db, room_id)
        for user in room_users:
            base_name = self._extract_ai_base_name(user.username)
            if base_name not in AI_NAMES:
                return True
        return False

    def all_players_active_in_room(self, db: Session, room_id: str) -> bool:
        room_users = self.get_room_users(db, room_id)
        if not room_users:
            return False

        for user in room_users:
            db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
            if not db_user or not db_user.is_active:
                print(f"Player {user.username} is not active")
                return False

        print(f"All {len(room_users)} players in room {room_id} are active")
        return True

    def broadcast_room_list_update(self, db: Session) -> None:
        rooms_data = self.get_rooms_data(db)
        users_not_in_room = (
            db.query(DBUser)
            .filter(DBUser.current_room_id == None, DBUser.is_active == True)
            .all()
        )

        for user in users_not_in_room:
            if user.username in self.sockets:
                user_socket_id = self.sockets[user.username]
                try:
                    self.socketio.emit(
                        "rooms_updated", {"rooms": rooms_data}, to=user_socket_id
                    )
                except Exception as e:
                    print(f"Error broadcasting to {user.username}: {e}")
                    self.sockets.pop(user.username, None)

    def get_room_model(self, db: Session, room_id: str) -> Optional[Room]:
        db_room = self.get_room_by_id(db, room_id)
        if not db_room:
            return None

        player_count = self.user_counter(db, room_id)

        return Room(
            room_id=room_id,
            name=db_room.name,
            max_player_count=db_room.max_player_count,
            password_protected=bool(db_room.password),
            player_count=player_count,
        )

    def get_client_users_in_room(self, db: Session, room_id: str) -> List[Client_User]:
        room_users = self.get_room_users(db, room_id)
        return [
            Client_User(username=r_u.username, is_active=r_u.is_active)
            for r_u in room_users
        ]

    @staticmethod
    def _extract_ai_base_name(name: str) -> str:
        from csotanypoker.models.user import AI_NAMES

        for ai_name in AI_NAMES:
            if name.startswith(ai_name):
                return ai_name
        return name
