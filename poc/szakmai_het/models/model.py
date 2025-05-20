from typing import Optional, List, Dict, Any


class Kartya:
    def __init__(self, tipus, sorszam):
        self._nev = f"{tipus}_{sorszam}"
        self._tipus = tipus
        self._sorszam = sorszam
        self._volt_ennel_mar = []

    @property
    def nev(self) -> str:
        return self._nev

    @nev.setter
    def nev(self, ertek: str) -> None:
        self._nev = ertek

    @property
    def tipus(self) -> str:
        return self._tipus

    @tipus.setter
    def tipus(self, ertek: str) -> None:
        self._tipus = ertek
        self._nev = f"{self._tipus}_{self._sorszam}"

    @property
    def sorszam(self) -> int:
        return self._sorszam

    @sorszam.setter
    def sorszam(self, ertek: int) -> None:
        self._sorszam = ertek
        self._nev = f"{self._tipus}_{self._sorszam}"

    @property
    def volt_ennel_mar(self) -> List:
        return self._volt_ennel_mar

    @volt_ennel_mar.setter
    def volt_ennel_mar(self, ertek: List) -> None:
        self._volt_ennel_mar = ertek

    @property
    def allat_tipus(self) -> str:
        return self._nev.split("_")[0]

    @allat_tipus.setter
    def allat_tipus(self, ertek: str) -> None:
        self._tipus = ertek
        self._nev = f"{ertek}_{self._sorszam}"


class Jatekos:
    def __init__(self, nev):
        self._nev = nev
        self._kezbenlevo_kartyak = []
        self._elotte_levo_kartyak = {}
        self._lapszam = 0
        self._allitas = None
        self._igaz_e = None

    @property
    def nev(self) -> str:
        return self._nev

    @nev.setter
    def nev(self, ertek: str) -> None:
        self._nev = ertek

    @property
    def kezbenlevo_kartyak(self) -> List:
        return self._kezbenlevo_kartyak

    @kezbenlevo_kartyak.setter
    def kezbenlevo_kartyak(self, ertek: List) -> None:
        self._kezbenlevo_kartyak = ertek

    @property
    def elotte_levo_kartyak(self) -> Dict:
        return self._elotte_levo_kartyak

    @elotte_levo_kartyak.setter
    def elotte_levo_kartyak(self, ertek: Dict) -> None:
        self._elotte_levo_kartyak = ertek

    @property
    def lapszam(self) -> int:
        return self._lapszam

    @lapszam.setter
    def lapszam(self, ertek: int) -> None:
        self._lapszam = ertek

    @property
    def allitas(self) -> Any:
        return self._allitas

    @allitas.setter
    def allitas(self, ertek: Any) -> None:
        self._allitas = ertek

    @property
    def igaz_e(self) -> bool:
        return self._igaz_e

    @igaz_e.setter
    def igaz_e(self, ertek: bool) -> None:
        self._igaz_e = ertek


class GameState:
    def __init__(self):
        self._jatekosok = []
        self._pakli = []
        self._aktiv_jatekos = None
        self._celzott_jatekos = None
        self._kerdeses_kartya: Optional[Kartya] = None

    @property
    def jatekosok(self) -> List[Jatekos]:
        return self._jatekosok

    @jatekosok.setter
    def jatekosok(self, ertek: List[Jatekos]) -> None:
        self._jatekosok = ertek

    @property
    def pakli(self) -> List[Kartya]:
        return self._pakli

    @pakli.setter
    def pakli(self, ertek: List[Kartya]) -> None:
        self._pakli = ertek

    @property
    def aktiv_jatekos(self) -> Optional[Jatekos]:
        return self._aktiv_jatekos

    @aktiv_jatekos.setter
    def aktiv_jatekos(self, ertek: Optional[Jatekos]) -> None:
        self._aktiv_jatekos = ertek

    @property
    def celzott_jatekos(self) -> Optional[Jatekos]:
        return self._celzott_jatekos

    @celzott_jatekos.setter
    def celzott_jatekos(self, ertek: Optional[Jatekos]) -> None:
        self._celzott_jatekos = ertek

    @property
    def kerdeses_kartya(self) -> Optional[Kartya]:
        return self._kerdeses_kartya

    @kerdeses_kartya.setter
    def kerdeses_kartya(self, ertek: Optional[Kartya]) -> None:
        self._kerdeses_kartya = ertek
