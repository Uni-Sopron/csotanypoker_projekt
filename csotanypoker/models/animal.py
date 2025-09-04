from enum import Enum


class Animal(Enum):
    COCKROACH = "cockroach"
    RAT = "rat"
    BAT = "bat"
    TOAD = "toad"
    BEDBUG = "bedbug"
    SPIDER = "spider"
    FLY = "fly"
    SCORPION = "scorpion"


    def __str__(self):
        return self.value
