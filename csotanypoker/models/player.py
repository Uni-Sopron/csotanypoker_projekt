from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# from csotanypoker.models.card import Card
from csotanypoker.models.animal import Animal


class AbstractPlayer(BaseModel):

    username: str = Field(..., description="Játékos felhasználónév")
    cards_in_front: Dict[Animal, int] = Field(default_factory=dict)
    statement: Optional[Animal] = Field(
        None, description="Állítás amit a kártyáról tett (állat típus)"
    )
    is_true: Optional[bool] = Field(
        None, description="A játékos szerint igaz vagy hamis az állítás"
    )

    def card_count(self) -> int:
        raise NotImplementedError


class VisiblePlayer(AbstractPlayer):  # saját játékos
    cards_in_hand: List[Animal] = Field(
        default_factory=list, description="Kézbeli kártyák"
    )

    def card_count(self) -> int:
        return len(self.cards_in_hand)


class OpponentPlayer(AbstractPlayer):  # ellenfel jatekos
    card_count_int: int = Field(default=0, description="Kártyák száma")

    def card_count(self) -> int:
        return self.card_count_int
