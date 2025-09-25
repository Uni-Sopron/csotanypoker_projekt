from pydantic import BaseModel, ConfigDict, Field


class Client_User(BaseModel):
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    username: str = Field(..., min_length=1, max_length=50)
    is_active: bool = Field(default=True)


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
