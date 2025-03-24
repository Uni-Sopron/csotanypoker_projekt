from sqlalchemy import create_engine, Column, String, ForeignKey, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

engine = create_engine("sqlite:///poc/asztalos_verzio/game.db")
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    username = Column(String(50), primary_key=True)
    socket_id = Column(String(100))
    current_room_id = Column(String(36), ForeignKey("rooms.room_id"),nullable=True)

    current_room = relationship("Room", back_populates="players")
    def set_current_room_id(self, room_id):
        self.current_room_id = room_id  

class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    game_started = Column(Boolean, default=False)
    player_count = Column(Integer, default=0)
    players = relationship("User", back_populates="current_room")

    def set_game_started(self, game_started):
        self.game_started = game_started
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def get_db_session():
    return Session()
