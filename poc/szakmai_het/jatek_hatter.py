from random import shuffle, choice
import os

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
    def __init__(self, jatekosok):
        self.jatekosok = jatekosok
        self.pakli = []
        self.aktiv_jatekos = self.kezdo_jatekos_sorsolasa()
        self.celzott_jatekos = jatekos
        self.kerdeses_kartya = kartya
        self.jatekos_allitasa = ""
        self.pakli_generalo()
        self.pakli_keveres()
        self.pakli_kiosztas()
        # self.jatek_ciklus()

    def pakli_generalo(self):
        for i in TIPUS:
            self.pakli.extend([kartya(i) for _ in range(8)])

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
        return self.aktiv_jatekos.kezbenlevo_kartyak != []

    def van_4_lap_elotte(self):
        for kartya, db in self.aktiv_jatekos.elotte_levo_kartyak.items():
            if db == 4:
                return True
        return False

    def celzott_jatekos_valasztas(self, nev):
        # nev=input("valasz egy jatekos nevet ")
        for i in self.jatekosok:
            if nev == i.nev:
                self.celzott_jatekos = i
                break

    def kartya_valasztas(self, valasztott_kartya_nev=None):
        # print("Válassz egy kártyát az alábbiak közül:")
        # print([kartya.nev for kartya in self.aktiv_jatekos.kezbenlevo_kartyak])

        # valasztott_kartya_nev = input("Kártya neve: ")

        # Megkeressük a játékos kezében lévő megfelelő kártyát
        for kartya in self.aktiv_jatekos.kezbenlevo_kartyak:
            if kartya.nev == valasztott_kartya_nev:
                self.kerdeses_kartya = kartya
                self.aktiv_jatekos.kezbenlevo_kartyak.remove(
                    kartya
                )  # Eltávolítjuk a kártyát
                return

        # print("Hibás választás! Nincs ilyen kártya a kezedben.")
        # self.kartya_valasztas()  # Újraválasztás

    def volt_e_nala(self):
        return self.celzott_jatekos in self.kerdeses_kartya.volt_ennel_mar

    def allitas(self, allitas=None):
        # print("csotany", "denever", "poloska","varangy", "patkány","pók","legy","skorpio")
        # allitas = input("Milyen állat? ")
        self.jatekos_allitasa = allitas
        if self.jatekos_allitasa == self.kerdeses_kartya.nev:
            # print("nem hazudsz")
            return "nem hazudsz"
        else:
            # print("hazudsz")
            return "hazudsz"

    def igaz_vagy_hamis(self, valasz):
        if valasz is True:
            if self.jatekos_allitasa == self.kerdeses_kartya.nev:
                print("jó válasz")
                return True
                # self.kartya_lerakas(self.aktiv_jatekos)
            else:
                print("rossz válasz")
                return False
                # self.kartya_lerakas(self.celzott_jatekos)
        elif valasz is False:
            if self.jatekos_allitasa != self.kerdeses_kartya.nev:
                print("jó válasz")
                return True
                # self.kartya_lerakas(self.aktiv_jatekos)
            else:
                print("rossz válasz")
                return False
                # self.kartya_lerakas(self.celzott_jatekos)

    def kartya_lerakas(self, jatekos):
        if self.kerdeses_kartya.nev not in jatekos.elotte_levo_kartyak:
            jatekos.elotte_levo_kartyak[self.kerdeses_kartya.nev] = 1
        else:
            jatekos.elotte_levo_kartyak[self.kerdeses_kartya.nev] += 1
        self.aktiv_jatekos = jatekos
        print("lerakás")
        # print("jatekos_elotte_kartyak", jatekos.elotte_levo_kartyak)

    def jatek_ciklus(self):
        while not self.van_4_lap_elotte() and self.van_lap_a_kezeben():
            # van a kezében kártya  ,és nincs elötte 4 ugyan olyan lap

            os.system("cls" if os.name == "nt" else "clear")  # Terminál törlése
            print(f"AKTIV JÁTÉKOS: {self.aktiv_jatekos.nev} ")
            print(f"Előtte lévő kártyák: {self.aktiv_jatekos.elotte_levo_kartyak}")
            # többi játékos
            print("TÖBBI JÁTÉKOSOK:")
            print(
                [
                    f"{jatekos.nev}"
                    for jatekos in self.jatekosok
                    if jatekos != self.aktiv_jatekos
                ]
            )
            self.kartya_valasztas()
            self.ciklus()

        print(f" VESZTES: {self.aktiv_jatekos.nev}")

    def ciklus(self):
        self.kerdeses_kartya.volt_ennel_mar.append(self.aktiv_jatekos)
        self.celzott_jatekos_valasztas()
        print(f"AKTIV JÁTÉKOS: {self.aktiv_jatekos.nev}")
        while self.volt_e_nala() or self.celzott_jatekos == self.aktiv_jatekos:
            print("volt már nala")
            self.celzott_jatekos_valasztas()
        self.allitas()

        print(
            "--------------------------------------------------------------------------------------------"
        )
        print("CÉLZOTT JÁTÉKOS:")
        print(self.celzott_jatekos.nev)
        print(f" Ez a kártya egy: {self.jatekos_allitasa}")

        print(
            f" ez a kártya kiknél volt: {[jatekos.nev for jatekos in self.kerdeses_kartya.volt_ennel_mar]}"
        )

        if (
            len(self.kerdeses_kartya.volt_ennel_mar) == len(self.jatekosok) - 1
            or len(self.jatekosok) == 2
        ):
            print("IGAZ , HAMIS")
        else:
            print("IGAZ , HAMIS, PASS")

        valasz = input("Valasz: ")
        if valasz == "pass":
            print(self.kerdeses_kartya.nev)
            self.aktiv_jatekos = self.celzott_jatekos
            return self.ciklus()
        elif valasz == "igaz":
            if self.jatekos_allitasa == self.kerdeses_kartya.nev:
                print("jó válasz")
                self.kartya_lerakas(self.aktiv_jatekos)
            else:
                print("rossz válasz")
                self.kartya_lerakas(self.celzott_jatekos)
        elif valasz == "hamis":
            if self.jatekos_allitasa != self.kerdeses_kartya.nev:
                print("jó válasz")
                self.kartya_lerakas(self.aktiv_jatekos)
            else:
                print("rossz válasz")
                self.kartya_lerakas(self.celzott_jatekos)

        # input()

        # self.celzott_jatekos_valasztas()

        # self.kartya_valasztas()


class jatekos:
    def __init__(self, nev):
        self.nev = nev
        self.kezbenlevo_kartyak = []
        self.elotte_levo_kartyak = {}

    pass


class kartya:
    def __init__(self, nev):
        self.nev = nev
        self.volt_ennel_mar = []  # [ jatekos.nev, jatekos.nev.. ]


# proba_jatek=jatek([jatekos("sanyi"),jatekos("pisti"),jatekos("jani")])

# Kiíratás listaként
# print([kartya.nev for kartya in proba_jatek.pakli])

# # Pakli méretének kiírása
# print(f"A pakliban {len(proba_jatek.pakli)} kártya van.")
# print([kartya.nev for kartya in proba_jatek.jatekosok[0].kezbenlevo_kartyak])
# print(len(proba_jatek.jatekosok[0].kezbenlevo_kartyak))
# print([kartya.nev for kartya in proba_jatek.jatekosok[1].kezbenlevo_kartyak])
# print(len(proba_jatek.jatekosok[1].kezbenlevo_kartyak))
# print([kartya.nev for kartya in proba_jatek.jatekosok[2].kezbenlevo_kartyak])
# print(len(proba_jatek.jatekosok[2].kezbenlevo_kartyak))
