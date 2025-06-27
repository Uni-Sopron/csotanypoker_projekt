from typing import Optional


from pydantic import BaseModel, Field, ConfigDict



class User(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # SQLAlchemy objektumokból is lehet példányosítani
        validate_assignment=True  # Validálja az értékadást
    )
    
    username: str = Field(..., min_length=1, max_length=50)
    password: Optional[str] = Field(None, max_length=100)
    current_room_id: Optional[str] = Field(None, max_length=50)
    is_active: bool = Field(default=True)