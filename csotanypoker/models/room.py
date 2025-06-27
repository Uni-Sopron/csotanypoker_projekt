from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Room(BaseModel):
    """
    Pydantic séma a Room osztályhoz (üzleti logika)
    """

    model_config = ConfigDict(
        from_attributes=True,
       
        extra="ignore",
    )

    room_id: str = Field(..., description="Egyedi szoba azonosító")
    name: str = Field(..., min_length=1, max_length=100, description="Szoba neve")
    game_ids: List[str] = Field(default_factory=list, description="Játék ID-k listája")
    max_player_count: int = Field(
        default=4, ge=1, le=10, description="Maximum játékosok száma"
    )
    password_protected: bool = Field(default=False, description="Jelszóval védett-e")
    password: Optional[str] = Field(None, description="Szoba jelszava")
    users: List[str] = Field(default_factory=list, description="Felhasználók listája")
    player_count: int = Field(default=0, ge=0, description="Jelenlegi játékosok száma")
