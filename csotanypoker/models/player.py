from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from csotanypoker.models.card import Card


class Player(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # objectumokból is lehet példányosítani nem csak dict-ből
        validate_assignment=True,  # értékadáskor is ellenörzi a mezők típusát
        extra="forbid",  # nem engedélyezi az ismeretlen mezőket
    )

    name: str
    cards_in_hand: List[Card] = Field(default_factory=list)
    cards_in_front: Dict[str, int] = Field(default_factory=dict)
    card_count: int = 0
    statement: Optional[str] = None  # allitás amit a kártyárol tett(allat tipus)
    is_true: Optional[bool] = (
        None  # a játékos szerint igaz vagy hamis az az állitás amit mondtak neki(true/false)
    )
