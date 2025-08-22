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


SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 700
FPS = 100

# Színek

BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)


RED = (164, 71, 69)  # a44745
WHITE = (255, 255, 255)
DARK_GREEN = (39, 40, 27)  # 27281b
LIGHT_GREEN = (134, 136, 104)  # 868868
MIDDLE_GREEN = (65, 67, 47)  # 41432f
LIGHTER_GREEN = (188, 191, 154)  # bc9f9a
# átlátszók:
LIGHT_GREEN_TRANSPARENT = (134, 136, 104, 204)  # 868868 80%
MIDDLE_GREEN_TRANSPARENT_90 = (65, 67, 47, 230)  # 41432f 90%
MIDDLE_GREEN_TRANSPARENT_70 = (65, 67, 47, 153)  # 41432f 70%
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
