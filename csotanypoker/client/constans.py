import os
import pygame

pygame.font.init()
# Font paths
FONT_PATH_REGULAR = os.path.join(
    "csotanypoker", "client", "fonts", "DrukaatieBurti-Regular.ttf"
)
FONT_PATH_BOLD = os.path.join(
    "csotanypoker", "client", "fonts", "DrukaatieBurti-Bold.ttf"
)
FONT_PATH_THIN = os.path.join(
    "csotanypoker", "client", "fonts", "DrukaatieBurti-Thin.ttf"
)

# Font sizes
FONT_SIZE_DEFAULT = 24
TITLE_FONT_SIZE = 60

SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 700
FPS = 5

# Színek

BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)

GREEN = (118, 153, 87)  # 769957
RED = (164, 71, 69)  # a44745
WHITE = (255, 255, 255)
DARK_GREEN = (39, 40, 27)  # 27281b
LIGHT_GREEN = (134, 136, 104)  # 868868
MIDDLE_GREEN = (65, 67, 47)  # 41432f
LIGHTER_GREEN = (188, 191, 154)  # bc9f9a
LEGVILÁGOS_ZÖLD = (212, 214, 191)  # d4d6bf
# átlátszók:
LEGVILÁGOS_ZÖLD_TRANSPARENT = (212, 214, 191, 204)  # d4d6bf 80%
LIGHTER_GREEN_TRANSPARENT = (188, 191, 154, 204)  # bc9f9a 80%
LIGHT_GREEN_TRANSPARENT = (134, 136, 104, 204)  # 868868 80%
MIDDLE_GREEN_TRANSPARENT_90 = (65, 67, 47, 230)  # 41432f 90%
MIDDLE_GREEN_TRANSPARENT_70 = (65, 67, 47, 153)  # 41432f 70%
MIDDLE_GREEN_TRANSPARENT_50 = (65, 67, 47, 102)  # 41432f 50%
DARK_GREEN_TRANSPARENT = (39, 40, 27, 204)  # 27281b 90%

# Betűméretek
FONT_SMALL = 20
FONT_MEDIUM = 24
CARD_BACK = "kerdojel"

# Állatok
ANIMALS = [
    "COCKROACH",
    "BAT",
    "BEDBUG",
    "RAT",
    "FLY",
    "TOAD",
    "SCORPION",
    "SPIDER",
]

JATEKSZABALY = {
    "2": """
Adj át egy kártyát az ellenfélnek és mondd meg mi van rajta (igazat vagy hazugságot).

Az ellenfél eldönti, hogy szerinte igaz-e. 
Ha eltalálja, te kapod vissza a kártyát, ha nem, nála marad. 
Aki végül megkapja a kártyát, az kezdi a következő kört.

Vesztesz, ha összegyűlik 5 ugyanolyan kártya előtted vagy elfogynak a kártyáid.""",
    "3-6": """
Adj át egy kártyát valakinek és mondd meg mi van rajta (igazat vagy hazugságot). 

A megcélzott játékos eldöntheti, hogy elfogadja és tippel, vagy továbbadja másnak.
Ha valaki tippel és eltalálja, a feladó kapja vissza a kártyát, ha nem, a tippelőnél marad.Aki végül megkapja a kártyát, az kezdi a következő kört. 

Vesztesz, ha összegyűlik 4 ugyanolyan kártya előtted vagy elfogynak a kártyáid.
""",
}
