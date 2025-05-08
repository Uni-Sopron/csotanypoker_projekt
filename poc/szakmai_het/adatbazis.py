from flask import json

from sqlalchemy import (
    create_engine,
    Column,
    String,
    ForeignKey,
    Boolean,
    Integer,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from typing import Optional


engine = create_engine("sqlite:///game.db")
Base = declarative_base()


# Asszociációs tábla Player és Card között (kézben lévő lapokhoz)
player_hand_cards = Table(
    "player_hand_cards",
    Base.metadata,
    Column("player_name", String(50), ForeignKey("players.name")),
    Column("card_name", String(100), ForeignKey("cards.name")),
)

# Asszociációs tábla Player és Card között (előtte lévő lapokhoz)
player_front_cards = Table(
    "player_front_cards",
    Base.metadata,
    Column("player_name", String(50), ForeignKey("players.name")),
    Column("card_name", String(100), ForeignKey("cards.name")),
)


# )
cardholders = Table(
    "cardholders",
    Base.metadata,
    Column("card_name", String, ForeignKey("cards.name"), primary_key=True),
    Column("player_name", String, ForeignKey("players.name"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    username = Column(
        String(50), primary_key=True
    )  # Felhasználónév mint elsődleges kulcs
    password = Column(String(100), nullable=True)
    current_room_id = Column(
        String(36), ForeignKey("rooms.room_id"), nullable=True
    )  # Aktuális szoba ID, külső kulcs a rooms táblához
    is_active = Column(Boolean, default=True)

    # Kapcsolat a Room osztállyal
    current_room = relationship("Room", back_populates="users")
    # Kapcsolat a Player osztállyal
    player = relationship("Player", back_populates="user", uselist=False)

    def set_current_room_id(self, room_id: Optional[str]) -> None:
        """
        Beállítja a felhasználó aktuális szoba azonosítóját.

        Args:
            room_id (Optional[str]): A felhasználó aktuális szobájának azonosítója.
        """
        self.current_room_id = room_id

    def set_active(self, active_status: bool) -> None:
        """
        Beállítja a felhasználó aktív státuszát.

        Args:
            active_status (bool): True ha a felhasználó be van jelentkezve, False ha nem.
        """
        self.is_active = active_status


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(
        String(36), primary_key=True
    )  # Egyedi szoba azonosító mint elsődleges kulcs
    name = Column(String(100), nullable=False)
    game_started = Column(Boolean, default=False)
    player_count = Column(
        Integer, default=4
    )  # Játékosok száma a szobában, alapértelmezetten 4

    # Kapcsolat a User osztállyal
    users = relationship("User", back_populates="current_room")
    # Kapcsolat a Game osztállyal
    game = relationship("Game", back_populates="room", uselist=False)

    def set_game_started(self, game_started: bool) -> None:
        """
        Beállítja a szoba játék állapotát.

        Args:
            game_started (bool): True ha a játék fut, False ha nem.
        """
        self.game_started = game_started


class Card(Base):
    __tablename__ = "cards"

    name = Column(String(100), primary_key=True)

    volt_ennel_mar = relationship(
        "Player", secondary=cardholders, backref="volt_nala_mar"
    )

    players_hand = relationship(
        "Player", secondary=player_hand_cards, back_populates="kezben_levo_lapok"
    )
    players_front = relationship(
        "Player", secondary=player_front_cards, back_populates="elotte_levo_kartyak"
    )

    questioned_in_games = relationship(
        "Game",
        foreign_keys="[Game.kerdeses_kartya_name]",
        back_populates="kerdeses_kartya",
    )

    def get_volt_ennel_mar(self):
        return json.loads(self.volt_ennel_mar)

    def add_volt_ennel_mar(self, player_name: str):
        lista = self.get_volt_ennel_mar()
        if player_name not in lista:
            lista.append(player_name)
            self.volt_ennel_mar = json.dumps(lista)


class Player(Base):
    __tablename__ = "players"

    name = Column(String(50), ForeignKey("users.username"), primary_key=True)
    allitas = Column(String(200), nullable=True)  # Állítás lehet üres is

    # Kapcsolatok a Card osztállyal asszociációs táblákon keresztül
    kezben_levo_lapok = relationship(
        "Card", secondary=player_hand_cards, back_populates="players_hand"
    )
    elotte_levo_kartyak = relationship(
        "Card", secondary=player_front_cards, back_populates="players_front"
    )

    # Kapcsolat a User osztállyal
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
    """
    Létrehoz és visszaad egy új adatbázis munkamenetet.

    Returns:
        Session: Új adatbázis munkamenet objektum.
    """
    return Session()
