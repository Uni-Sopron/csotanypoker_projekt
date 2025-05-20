from random import shuffle, choice
from sqlalchemy.orm import Session
from adatbazis import Card, Player, get_db_session
import sys
import os
sys.path.append(os.path.abspath('..')) 
from models.model import Kartya,  GameState


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
        self.state = GameState()

        self.state.jatekosok = jatekosok
        self.state.aktiv_jatekos = self.kezdo_jatekos_sorsolasa()
        self.pakli_generalo()
        self.pakli_keveres()
        self.pakli_kiosztas()

    def pakli_generalo(self):
        for tipus in TIPUS:
            for i in range(1, 9):
                self.state.pakli.append(Kartya(tipus, i))

    def pakli_keveres(self):
        shuffle(self.state.pakli)
        if len(self.state.jatekosok) == 2:
            self.state.pakli = self.state.pakli[:-10]

    def pakli_kiosztas(self):
        jatekos_szam = len(self.state.jatekosok)
        pakli_meret = len(self.state.pakli)
        reszek = pakli_meret // jatekos_szam
        for i in range(jatekos_szam):
            self.state.jatekosok[i].kezbenlevo_kartyak = self.state.pakli[
                i * reszek : (i + 1) * reszek
            ]

    def kezdo_jatekos_sorsolasa(self):
        return choice(self.state.jatekosok)

    def van_lap_a_kezeben(self):
        return self.state.aktiv_jatekos.kezbenlevo_kartyak == []

    def van_4_lap_elotte(self):
        for kartya, db in self.state.aktiv_jatekos.elotte_levo_kartyak.items():
            if db == 4:
                return True
        return False

    def celzott_jatekos_valasztas(self, nev):
        for i in self.state.jatekosok:
            if nev == i.nev:
                self.state.celzott_jatekos = i
                break

    def kartya_valasztas(self, valasztott_kartya_id=None):
        db: Session = get_db_session()
        jatekos_db = (
            db.query(Player).filter(Player.name == self.state.aktiv_jatekos.nev).first()
        )

        for kartya in self.state.aktiv_jatekos.kezbenlevo_kartyak:
            if kartya.nev == valasztott_kartya_id:
                self.state.kerdeses_kartya = kartya
                kivalasztott_kartya = (
                    db.query(Card)
                    .filter(Card.name == self.state.kerdeses_kartya.nev)
                    .first()
                )
                self.state.aktiv_jatekos.kezbenlevo_kartyak.remove(
                    kartya
                )  # Eltávolítjuk a kártyát
                if (
                    self.state.aktiv_jatekos.nev
                    not in self.state.kerdeses_kartya.volt_ennel_mar
                ):
                    self.state.kerdeses_kartya.volt_ennel_mar.append(
                        self.state.aktiv_jatekos.nev
                    )
                    kivalasztott_kartya.volt_ennel_mar.append(jatekos_db)
                    db.commit()
                return

    def allitas(self, allitas=None):
        db: Session = get_db_session()
        player = (
            db.query(Player).filter(Player.name == self.state.aktiv_jatekos.nev).first()
        )
        player.allitas = allitas
        db.commit()
        self.state.aktiv_jatekos.allitas = allitas  # Az aktuális játékos állítása

    def igaz_vagy_hamis(self, valasz):
        self.state.celzott_jatekos.igaz_e = valasz  # Az aktuális játékos válasza
        if self.state.celzott_jatekos.igaz_e is True:
            if (
                self.state.aktiv_jatekos.allitas
                == self.state.kerdeses_kartya.allat_tipus
            ):
                print("jó válasz")
                return True

            else:
                print("rossz válasz")
                return False

        elif self.state.celzott_jatekos.igaz_e is False:
            if (
                self.state.aktiv_jatekos.allitas
                != self.state.kerdeses_kartya.allat_tipus
            ):
                print("jó válasz")
                return True

            else:
                print("rossz válasz")
                return False

    def kartya_lerakas(self, jatekos):
        db: Session = get_db_session()
        kivalasztott_kartya = (
            db.query(Card).filter(Card.name == self.state.kerdeses_kartya.nev).first()
        )
        jatekos_db = db.query(Player).filter(Player.name == jatekos.nev).first()
        jatekos_db.elotte_levo_kartyak.append(kivalasztott_kartya)

        db.commit()

        if self.state.kerdeses_kartya.allat_tipus not in jatekos.elotte_levo_kartyak:
            jatekos.elotte_levo_kartyak[self.state.kerdeses_kartya.allat_tipus] = 1

        else:
            jatekos.elotte_levo_kartyak[self.state.kerdeses_kartya.allat_tipus] += 1

        self.state.aktiv_jatekos = jatekos
