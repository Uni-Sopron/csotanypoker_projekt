from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_serializer
from csotanypoker.models.animal import Animal


class AbstractPlayer(BaseModel):
    username: str = Field(...)
    cards_in_front: Dict[Animal, int] = Field(default_factory=lambda: {})
    statement: Optional[Animal] = Field(None)
    is_true: Optional[bool] = Field(None)

    @field_serializer("cards_in_front")
    def serialize_cards_in_front(self, value: Dict[Animal, int]) -> Dict[str, int]:
        """
        Converts Animal enums to strings for JSON serialization.

        Args:
            value (Dict[Animal, int]): Contains how many of each animal are in front of the player.

        Returns:
            Dict[str, int]: Dictionary with string keys and integer counts
        """
        return {str(animal): count for animal, count in value.items()}

    def card_count(self) -> int:
        """
        Returns the number of cards in hand. Implemented by subclasses.

        Returns:
            int: Number of cards in hand

        """
        raise NotImplementedError


class VisiblePlayer(AbstractPlayer):
    cards_in_hand: List[Animal] = Field(
        default_factory=list, description="Kézbeli kártyák"
    )

    @field_serializer("cards_in_hand")
    def serialize_cards_in_hand(self, value: List[Animal]) -> List[str]:
        """
        Converts Animal enums to strings for JSON serialization.

        Args:
            value (List[Animal]): List of Animal enum objects

        Returns:
            List[str]: List of animal names as strings
        """
        return [str(animal) for animal in value]

    def card_count(self) -> int:
        """
        Returns the number of cards in hand.

        Returns:
            int: Number of cards in the cards_in_hand list
        """
        return len(self.cards_in_hand)


class OpponentPlayer(AbstractPlayer):
    card_count_int: int = Field(default=0, description="Kártyák száma")

    def card_count(self) -> int:
        """
        Returns the number of cards in hand.

        Returns:
            int: Number of cards stored in card_count_int
        """
        return self.card_count_int
