from random import shuffle
TIPUS=["csotany", "denever", "poloska", "patkany", "légy", "varangy", "skorpió","pók"]
class jatekos:
    def __init__(self, nev, client=None, addr=None):
        self.nev = nev
        self.client = client
        self.addr = addr
        self.kezbenlevo_kartyak = []
        self.elotte_levo_kartyak = {}
class jatek():
    def __init__(self,jatekosok):

        self.jatekosok = jatekosok
        self.pakli = []

        self.celzott_jatekos = jatekos
        self.kerdeses_kartya = kartya
        self.jatekos_allitasa = ""
        self.pakli_generalo()
        self.pakli_keveres()
        self.pakli_kiosztas()


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
        reszek= pakli_meret//jatekos_szam
        for i in range(jatekos_szam):
            self.jatekosok[i].kezbenlevo_kartyak = self.pakli[i*reszek:(i+1)*reszek]



class kartya:
    def __init__(self, nev):
        self.nev = nev
        self.volt_ennel_mar =[] 
