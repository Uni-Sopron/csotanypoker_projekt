from sqlalchemy import create_engine, Column, String, ForeignKey, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from typing import Optional


engine = create_engine("sqlite:///game.db")
Base = declarative_base()  # Create a base class for ORM models


class User(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)  # Username as the primary key
    socket_id = Column(String(100))
    current_room_id = Column(
        String(36), ForeignKey("rooms.room_id"), nullable=True
    )  # Current room ID, foreign key to the rooms table
    is_active = Column(Boolean, default=True)

    # Define relationship with the Room class
    current_room = relationship("Room", back_populates="players")

    def set_current_room_id(self, room_id: Optional[str]) -> None:
        """
        Sets the user's current room ID.

        Args:
            room_id (Optional[str]): The ID of the user's current room.
        """
        self.current_room_id = room_id

    def set_active(self, active_status: bool) -> None:
        """
        Sets the user's active status.

        Args:
            active_status (bool): True if the user is logged in, False if not.
        """
        self.is_active = active_status


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String(36), primary_key=True)  # Unique room ID as the primary key
    name = Column(String(100), nullable=False)
    game_started = Column(Boolean, default=False)
    player_count = Column(
        Integer, default=4
    )  # Number of players in a room, default is 3

    # Define relationship with the User class
    players = relationship("User", back_populates="current_room")

    def set_game_started(self, game_started: bool) -> None:
        """
        Sets the room's game state.

        Args:
            game_started (bool): True if the game is running, False if not.
        """
        self.game_started = game_started


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def get_db_session() -> Session:
    """
    Creates and returns a new database session.

    Returns:
        Session: New database session object.
    """
    return Session()
