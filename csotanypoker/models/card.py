from typing import List
from pydantic import BaseModel, Field, computed_field, ConfigDict


class Card(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, #objectumokból is lehet példányosítani nem csak dict-ből
        validate_assignment=True, # értékadáskor is ellenörzi a mezők típusát
        extra="forbid" # nem engedélyezi az ismeretlen mezőket
    )

    type: str
    index: int
    visited_already: List[str] = Field(default_factory=list)

    @computed_field # automatikusan számított mező
    @property
    def name(self) -> str:
        return f"{self.type}_{self.index}"

  