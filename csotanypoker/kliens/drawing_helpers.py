import pygame
import os
from csotanypoker.kliens.colors_and_sizes import FONT_SMALL


def draw_text(surface, text, color, x, y, centered=False, font=None):
    if font is None:
        font = pygame.font.Font(None, FONT_SMALL)
    text_surface = font.render(str(text), True, color)
    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
    surface.blit(text_surface, text_rect)


def load_image(name, scale_ratio=None, size=None, logo=False):
    if logo:
        path = os.path.join("csotanypoker", "kliens", "kepek", f"{name}_logo.png")
    else:
        path = os.path.join("csotanypoker", "kliens", "kepek", f"{name}.png")

    image = pygame.image.load(path).convert_alpha()

    if scale_ratio is not None:
        original_size = image.get_size()
        size = (
            int(original_size[0] * scale_ratio),
            int(original_size[1] * scale_ratio),
        )

    if size:
        image = pygame.transform.scale(image, size)

    return image


def draw_image(surface, image, x, y, size=None, centered=False):
    if size:
        image = pygame.transform.scale(image, size)
    rect = image.get_rect()
    if centered:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)
