import os

import pygame

from csotanypoker.client.constans import FONT_SMALL


def draw_text(surface, text, color, x, y, centered=False, font=None, vcenter_rect=None):
    if font is None:
        font = pygame.font.Font(None, FONT_SMALL)
    text_surface = font.render(str(text), True, color)

    if vcenter_rect is not None:
        text_height = text_surface.get_height()
        y = vcenter_rect.y + (vcenter_rect.height - text_height) // 2

    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
    surface.blit(text_surface, text_rect)


def load_image(
    name,
    type,
    scale_ratio=None,
    size=None,
):
    if type == "logo":
        path = os.path.join(
            "csotanypoker", "client", "images", "logos", f"{name}_logo.png"
        )
    elif type == "card":
        path = os.path.join("csotanypoker", "client", "images", "cards", f"{name}.png")
    elif type == "button":
        path = os.path.join(
            "csotanypoker", "client", "images", "ui-elements", "buttons", f"{name}.png"
        )
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
