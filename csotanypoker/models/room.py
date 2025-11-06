from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Room(BaseModel):
    """
    Pydantic séma a Room osztályhoz 
    """

    model_config = ConfigDict(
        from_attributes=True,
       
        extra="ignore",
    )

    room_id: str = Field(..., description="Egyedi szoba azonosító")
    name: str = Field(..., min_length=1, max_length=100, description="Szoba neve")
    password_protected: bool = Field(default=False, description="Jelszóval védett-e")
    player_count: int = Field(default=0, ge=0, description="Jelenlegi játékosok száma")
    max_player_count: int = Field(
        default=4, ge=1, le=10, description="Maximum játékosok száma"
    )
