from typing import Optional

from sqlalchemy import (Boolean, Column, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

engine = create_engine("sqlite:///game.db")
Base = declarative_base()


class PlayerHandCard(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __tablename__ = "player_hand_cards"
    player_name = Column(String(50), ForeignKey("players.name"), primary_key=True)
    card_name = Column(String(100), ForeignKey("cards.name"), primary_key=True)

    player = relationship("DBPlayer", back_populates="hand_card_links")
    card = relationship("DBCard", back_populates="hand_card_links")


class PlayerFrontCard(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __tablename__ = "player_front_cards"
    player_name = Column(String(50), ForeignKey("players.name"), primary_key=True)
    card_name = Column(String(100), ForeignKey("cards.name"), primary_key=True)

    player = relationship("DBPlayer", back_populates="front_card_links")
    card = relationship("DBCard", back_populates="front_card_links")


class CardHolder(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __tablename__ = "cardholders"
    card_name = Column(String(100), ForeignKey("cards.name"), primary_key=True)
    player_name = Column(String(50), ForeignKey("players.name"), primary_key=True)

    card = relationship("DBCard", back_populates="previous_holder_links")
    player = relationship("DBPlayer", back_populates="previously_held_card_links")


class DBUser(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)
    password = Column(String(100), nullable=True)
    current_room_id = Column(String(36), ForeignKey("rooms.room_id"), nullable=True)
    is_active = Column(Boolean, default=True)

    current_room = relationship("DBRoom", back_populates="users")
    player = relationship("DBPlayer", back_populates="user", uselist=False)

    def set_current_room_id(self, room_id: Optional[str]) -> None:
        self.current_room_id = room_id

    def set_active(self, active_status: bool) -> None:
        self.is_active = active_status


class DBRoom(Base):
    __tablename__ = "rooms"

    room_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    game_started = Column(Boolean, default=False)
    player_count = Column(Integer, default=4)
    password = Column(String(100), default=None, nullable=True)
    users = relationship("DBUser", back_populates="current_room")
    game = relationship("Game", back_populates="room", uselist=False)

    def set_game_started(self, game_started: bool) -> None:
        self.game_started = game_started


class DBCard(Base):
    __tablename__ = "cards"

    name = Column(String(100), primary_key=True)

    hand_card_links = relationship("PlayerHandCard", back_populates="card")
    front_card_links = relationship("PlayerFrontCard", back_populates="card")
    previous_holder_links = relationship("CardHolder", back_populates="card")

    players_hand = association_proxy("hand_card_links", "player")
    players_front = association_proxy("front_card_links", "player")
    previous_holders = association_proxy(
        "previous_holder_links",
        "player",
        creator=lambda player: CardHolder(player=player),
    )

    questioned_in_games = relationship(
        "Game",
        foreign_keys="[Game.questioned_card_name]",
        back_populates="questioned_card",
    )

    def get_previous_holders(self):
        return [player.name for player in self.previous_holders]

    def add_previous_holder(self, player):
        if player not in self.previous_holders:
            self.previous_holders.append(player)


class DBPlayer(Base):
    __tablename__ = "players"

    name = Column(String(50), ForeignKey("users.username"), primary_key=True)
    statement = Column(String(200), nullable=True)

    hand_card_links = relationship(
        "PlayerHandCard", back_populates="player", cascade="all, delete-orphan"
    )

    hand_cards = association_proxy(
        "hand_card_links",
        "card",
        creator=lambda card: PlayerHandCard(card=card),
    )
    front_card_links = relationship("PlayerFrontCard", back_populates="player")
    previously_held_card_links = relationship("CardHolder", back_populates="player")

    front_cards = association_proxy(
        "front_card_links",
        "card",
        creator=lambda card: PlayerFrontCard(card=card),
    )
    previously_held_cards = association_proxy(
        "previously_held_card_links", "card", creator=lambda card: CardHolder(card=card)
    )

    user = relationship("DBUser", back_populates="player")
    active_in_games = relationship(
        "Game", foreign_keys="[Game.active_player_name]", back_populates="active_player"
    )
    targeted_in_games = relationship(
        "Game",
        foreign_keys="[Game.target_player_name]",
        back_populates="target_player",
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(36), ForeignKey("rooms.room_id"), nullable=False)
    active_player_name = Column(String(50), ForeignKey("players.name"), nullable=True)
    target_player_name = Column(String(50), ForeignKey("players.name"), nullable=True)
    questioned_card_name = Column(String(100), ForeignKey("cards.name"), nullable=True)
    loser = Column(String(50), ForeignKey("players.name"), nullable=True)

    room = relationship("DBRoom", back_populates="game")
    active_player = relationship(
        "DBPlayer", foreign_keys=[active_player_name], back_populates="active_in_games"
    )
    target_player = relationship(
        "DBPlayer",
        foreign_keys=[target_player_name],
        back_populates="targeted_in_games",
    )
    questioned_card = relationship(
        "DBCard",
        foreign_keys=[questioned_card_name],
        back_populates="questioned_in_games",
    )


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def get_db_session() -> Session:
    return Session()
