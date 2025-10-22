import os
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Integer,
    Boolean,
    create_engine,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# engine = create_engine("sqlite:///game.db")
DATA_DIR = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '.')
engine = create_engine(f"sqlite:///{DATA_DIR}/game.db")
Base = declarative_base()

Users_in_Game = Table(
    "Users_in_Game",
    Base.metadata,
    Column("game_id", String(50), ForeignKey("games.game_id"), primary_key=True),
    Column("username", String(50), ForeignKey("users.username"), primary_key=True),
)


class DBUser(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)
    password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    current_room_id = Column(String(50), ForeignKey("rooms.room_id"), nullable=True)

    current_room = relationship("DBRoom", back_populates="current_users")
    games = relationship("DBGame", secondary=Users_in_Game, back_populates="players")


class DBRoom(Base):
    __tablename__ = "rooms"
    room_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    max_player_count = Column(Integer, default=4)
    password_protected = Column(Boolean, default=False)
    password = Column(String(100), nullable=True)

    current_users = relationship("DBUser", back_populates="current_room")
    games = relationship("DBGame", back_populates="room")


class DBGame(Base):
    __tablename__ = "games"
    game_id = Column(String(50), primary_key=True)
    loser_username = Column(String(50), nullable=True)
    game_status = Column(String(10), default="run")  # "run" vagy "end"
    room_id = Column(String(50), ForeignKey("rooms.room_id"), nullable=False)

    room = relationship("DBRoom", back_populates="games")
    players = relationship("DBUser", secondary=Users_in_Game, back_populates="games")


def get_db_session():
    Session = sessionmaker(bind=engine)
    return Session()


def create_tables():
    Base.metadata.create_all(engine)
