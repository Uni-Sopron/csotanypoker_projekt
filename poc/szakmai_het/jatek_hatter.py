from random import shuffle, choice
from sqlalchemy.orm import Session
from adatbazis import Card, Player, get_db_session


TIPUS = [
    "csotany",
    "denever",
    "poloska",
    "patkany",
    "légy",
    "varangy",
    "skorpió",
    "pók",
]


class jatek:
    def __init__(self, jatekosok, from_db=False):
        self.jatekosok = jatekosok
        self.pakli = []
        self.aktiv_jatekos = None
        self.celzott_jatekos = None
        self.kerdeses_kartya = None

        self.aktiv_jatekos = self.kezdo_jatekos_sorsolasa()
        self.pakli_generalo()
        self.pakli_keveres()
        self.pakli_kiosztas()

    def pakli_generalo(self):
        for tipus in TIPUS:
            for i in range(1, 9):
                self.pakli.append(kartya(tipus, i))

    def pakli_keveres(self):
        shuffle(self.pakli)
        if len(self.jatekosok) == 2:
            self.pakli = self.pakli[:-10]

    def pakli_kiosztas(self):
        jatekos_szam = len(self.jatekosok)
        pakli_meret = len(self.pakli)
        reszek = pakli_meret // jatekos_szam
        for i in range(jatekos_szam):
            self.jatekosok[i].kezbenlevo_kartyak = self.pakli[
                i * reszek : (i + 1) * reszek
            ]

    def kezdo_jatekos_sorsolasa(self):
        return choice(self.jatekosok)

    def van_lap_a_kezeben(self):
        return self.aktiv_jatekos.kezbenlevo_kartyak == []

    def van_4_lap_elotte(self):
        for kartya, db in self.aktiv_jatekos.elotte_levo_kartyak.items():
            if db == 4:
                return True
        return False

    def celzott_jatekos_valasztas(self, nev):
        for i in self.jatekosok:
            if nev == i.nev:
                self.celzott_jatekos = i
                break

    def kartya_valasztas(self, valasztott_kartya_id=None):
        db: Session = get_db_session()
        jatekos_db = (
            db.query(Player).filter(Player.name == self.aktiv_jatekos.nev).first()
        )

        for kartya in self.aktiv_jatekos.kezbenlevo_kartyak:
            if kartya.nev == valasztott_kartya_id:
                self.kerdeses_kartya = kartya
                kivalasztott_kartya = (
                    db.query(Card).filter(Card.name == self.kerdeses_kartya.nev).first()
                )
                self.aktiv_jatekos.kezbenlevo_kartyak.remove(
                    kartya
                )  # Eltávolítjuk a kártyát
                if self.aktiv_jatekos.nev not in self.kerdeses_kartya.volt_ennel_mar:
                    self.kerdeses_kartya.volt_ennel_mar.append(self.aktiv_jatekos.nev)
                    kivalasztott_kartya.volt_ennel_mar.append(jatekos_db)
                    db.commit()
                return

    def allitas(self, allitas=None):
        db: Session = get_db_session()
        player = db.query(Player).filter(Player.name == self.aktiv_jatekos.nev).first()
        player.allitas = allitas
        db.commit()
        self.aktiv_jatekos.allitas = allitas  # Az aktuális játékos állítása

    def igaz_vagy_hamis(self, valasz):
        self.celzott_jatekos.igaz_e = valasz  # Az aktuális játékos válasza
        if self.celzott_jatekos.igaz_e is True:
            if self.aktiv_jatekos.allitas == self.kerdeses_kartya.allat_tipus:
                print("jó válasz")
                return True

            else:
                print("rossz válasz")
                return False

        elif self.celzott_jatekos.igaz_e is False:
            if self.aktiv_jatekos.allitas != self.kerdeses_kartya.allat_tipus:
                print("jó válasz")
                return True

            else:
                print("rossz válasz")
                return False

    def kartya_lerakas(self, jatekos):
        db: Session = get_db_session()
        kivalasztott_kartya = (
            db.query(Card).filter(Card.name == self.kerdeses_kartya.nev).first()
        )
        jatekos_db = db.query(Player).filter(Player.name == jatekos.nev).first()
        jatekos_db.elotte_levo_kartyak.append(kivalasztott_kartya)

        db.commit()

        if self.kerdeses_kartya.allat_tipus not in jatekos.elotte_levo_kartyak:
            jatekos.elotte_levo_kartyak[self.kerdeses_kartya.allat_tipus] = 1

        else:
            jatekos.elotte_levo_kartyak[self.kerdeses_kartya.allat_tipus] += 1

        self.aktiv_jatekos = jatekos


class jatekos:
    def __init__(self, nev):
        self.nev = nev
        self.kezbenlevo_kartyak = []
        self.elotte_levo_kartyak = {}
        self.allitas = None  # Kezdetben nincs állítás
        self.igaz_e = None  # Kezdetben nincs tipp


class kartya:
    def __init__(self, tipus, sorszam):
        self.nev = f"{tipus}_{sorszam}"
        self.volt_ennel_mar = []

    @property
    def allat_tipus(self):
        return self.nev.split("_")[0]
