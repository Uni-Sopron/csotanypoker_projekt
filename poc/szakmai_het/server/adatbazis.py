from sqlalchemy import (
    create_engine,
    Column,
    String,
    ForeignKey,
    Boolean,
    Integer,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.associationproxy import association_proxy
from typing import Optional
engine = create_engine("sqlite:///game.db")
Base = declarative_base()


class PlayerHandCard(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    __tablename__ = "player_hand_cards"
    player_name = Column(String(50), ForeignKey("players.name"), primary_key=True)
    card_name = Column(String(100), ForeignKey("cards.name"), primary_key=True)

    player = relationship("Player", back_populates="kezben_levo_kapcsolatok")
    card = relationship("Card", back_populates="kezben_levo_kapcsolatok")


class PlayerFrontCard(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    __tablename__ = "player_front_cards"
    player_name = Column(String(50), ForeignKey("players.name"), primary_key=True)
    card_name = Column(String(100), ForeignKey("cards.name"), primary_key=True)

    player = relationship("Player", back_populates="elotte_levo_kapcsolatok")
    card = relationship("Card", back_populates="elotte_levo_kapcsolatok")


class CardHolder(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    __tablename__ = "cardholders"
    card_name = Column(String(100), ForeignKey("cards.name"), primary_key=True)
    player_name = Column(String(50), ForeignKey("players.name"), primary_key=True)

    card = relationship("Card", back_populates="volt_ennel_kapcsolatok")
    player = relationship("Player", back_populates="volt_nala_kapcsolatok")


class User(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)
    password = Column(String(100), nullable=True)
    current_room_id = Column(String(36), ForeignKey("rooms.room_id"), nullable=True)
    is_active = Column(Boolean, default=True)

    current_room = relationship("Room", back_populates="users")
    player = relationship("Player", back_populates="user", uselist=False)

    def set_current_room_id(self, room_id: Optional[str]) -> None:
        self.current_room_id = room_id

    def set_active(self, active_status: bool) -> None:
        self.is_active = active_status


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    game_started = Column(Boolean, default=False)
    player_count = Column(Integer, default=4)

    users = relationship("User", back_populates="current_room")
    game = relationship("Game", back_populates="room", uselist=False)

    def set_game_started(self, game_started: bool) -> None:
        self.game_started = game_started


class Card(Base):
    __tablename__ = "cards"

    name = Column(String(100), primary_key=True)

    kezben_levo_kapcsolatok = relationship("PlayerHandCard", back_populates="card")
    elotte_levo_kapcsolatok = relationship("PlayerFrontCard", back_populates="card")
    volt_ennel_kapcsolatok = relationship("CardHolder", back_populates="card")

    players_hand = association_proxy("kezben_levo_kapcsolatok", "player")
    players_front = association_proxy("elotte_levo_kapcsolatok", "player")
    volt_ennel_mar = association_proxy(
    "volt_ennel_kapcsolatok",
    "player",
    creator=lambda player: CardHolder(player=player)
)

    questioned_in_games = relationship(
        "Game",
        foreign_keys="[Game.kerdeses_kartya_name]",
        back_populates="kerdeses_kartya",
    )

    def get_volt_ennel_mar(self):
        return [player.name for player in self.volt_ennel_mar]

    def add_volt_ennel_mar(self, player):
        if player not in self.volt_ennel_mar:
            self.volt_ennel_mar.append(player)


class Player(Base):
    __tablename__ = "players"

    name = Column(String(50), ForeignKey("users.username"), primary_key=True)
    allitas = Column(String(200), nullable=True)

    kezben_levo_kapcsolatok = relationship("PlayerHandCard", back_populates="player", cascade="all, delete-orphan")

    kezben_levo_lapok = association_proxy(
        "kezben_levo_kapcsolatok",
        "card",
        creator=lambda card: PlayerHandCard(card=card)
    )
    elotte_levo_kapcsolatok = relationship("PlayerFrontCard", back_populates="player")
    volt_nala_kapcsolatok = relationship("CardHolder", back_populates="player")

   
    elotte_levo_kartyak = association_proxy(
    "elotte_levo_kapcsolatok",
    "card",
    creator=lambda card: PlayerFrontCard(card=card)
)
    volt_nala_mar = association_proxy(
    "volt_nala_kapcsolatok",
    "card",
    creator=lambda card: CardHolder(card=card)
)

    user = relationship("User", back_populates="player")
    active_in_games = relationship(
        "Game", foreign_keys="[Game.aktiv_jatekos_name]", back_populates="aktiv_jatekos"
    )
    targeted_in_games = relationship(
        "Game",
        foreign_keys="[Game.celzott_jatekos_name]",
        back_populates="celzott_jatekos",
    )


class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(36), ForeignKey("rooms.room_id"), nullable=False)
    aktiv_jatekos_name = Column(String(50), ForeignKey("players.name"), nullable=True)
    celzott_jatekos_name = Column(String(50), ForeignKey("players.name"), nullable=True)
    kerdeses_kartya_name = Column(String(100), ForeignKey("cards.name"), nullable=True)
    nyertes = Column(String(50), ForeignKey("players.name"), nullable=True)

    room = relationship("Room", back_populates="game")
    aktiv_jatekos = relationship(
        "Player", foreign_keys=[aktiv_jatekos_name], back_populates="active_in_games"
    )
    celzott_jatekos = relationship(
        "Player",
        foreign_keys=[celzott_jatekos_name],
        back_populates="targeted_in_games",
    )
    kerdeses_kartya = relationship(
        "Card",
        foreign_keys=[kerdeses_kartya_name],
        back_populates="questioned_in_games",
    )


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session() -> Session:
    return Session()