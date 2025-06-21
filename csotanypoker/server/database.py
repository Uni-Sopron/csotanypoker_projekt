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
from sqlalchemy.orm import relationship

engine = create_engine("sqlite:///game.db")
Base = declarative_base()

room_user_association = Table(
    "room_user_association",
    Base.metadata,
    Column("room_id", String(50), ForeignKey("rooms.room_id"), primary_key=True),
    Column("username", String(50), ForeignKey("users.username"), primary_key=True),
)

room_game_association = Table(
    "room_game_association",
    Base.metadata,
    Column("room_id", String(50), ForeignKey("rooms.room_id"), primary_key=True),
    Column("game_id", String(50), ForeignKey("games.id"), primary_key=True),
)


class DBUser(Base):
    __tablename__ = "users"

    username = Column(String(50), primary_key=True)
    password = Column(String(100), nullable=True)
    current_room_id = Column(String(50), ForeignKey("rooms.room_id"), nullable=True)
    is_active = Column(Boolean, default=True)

    current_room = relationship("DBRoom", back_populates="users")
    rooms_in = relationship(
        "DBRoom", secondary=room_user_association, back_populates="users_in_room"
    )



class DBRoom(Base):
    __tablename__ = "rooms"

    room_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    password = Column(String(100), nullable=True)
    password_protected = Column(Boolean, default=False)
    max_player_count = Column(Integer, default=4)
    player_count = Column(Integer, default=0)

    users = relationship("DBUser", back_populates="current_room")

  
    game_ids = relationship(
        "Game", secondary=room_game_association, back_populates="rooms_played_in"
    )

    users_in_room = relationship(
        "DBUser", secondary=room_user_association, back_populates="rooms_in"
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(String(50), primary_key=True)
    game_status = Column(String(10), default="run")  # 'run' vagy 'end'
    loser_username = Column(String(50), nullable=True)

    rooms_played_in = relationship(
        "DBRoom", secondary=room_game_association, back_populates="game_ids"
    )




def create_tables():
    Base.metadata.create_all(engine)
