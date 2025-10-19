from pydantic import BaseModel, ConfigDict, Field


class Client_User(BaseModel):
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    username: str = Field(..., min_length=1, max_length=50)
    is_active: bool = Field(default=True)


def this_is_ai_name(name: str) -> str:
    for ai_name in AI_NAMES:
        if name.startswith(ai_name):
            return ai_name

    return name
AI_NAMES = [
    "HazugCsóti",
    "Kamucsótány",
    "Lapátadó",
    "Poloskakirály",
    "Hálócsapda",
    "HazudósBélus",
    "SunyiJóska",
    "KártyásFeri",
    "LaplopóLajos",
    "BlöffBandi",
    "ÁtverőPisti",
    "ZümmZoli",
    "CsótányKarcsi",
    
]
