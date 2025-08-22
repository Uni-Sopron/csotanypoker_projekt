import os
import pygame
from typing import Union

from csotanypoker.client.constans import (
    FONT_SIZE_DEFAULT,
    FONT_PATH_REGULAR,
    FONT_PATH_BOLD,
    FONT_PATH_THIN,
    WHITE,
    DARK_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    MIDDLE_GREEN,
)


_font_cache = {}


def _get_font(
    font_type: Union[str, pygame.font.Font], font_size: int = None
) -> pygame.font.Font:
    if font_size is None:
        font_size = FONT_SIZE_DEFAULT

    if isinstance(font_type, pygame.font.Font):
        if font_size == FONT_SIZE_DEFAULT:
            return font_type
        font_path = getattr(font_type, "_name", FONT_PATH_REGULAR)
    else:
        font_paths = {
            "regular": FONT_PATH_REGULAR,
            "bold": FONT_PATH_BOLD,
            "thin": FONT_PATH_THIN,
        }
        font_path = font_paths.get(str(font_type).lower(), FONT_PATH_REGULAR)

    cache_key = (font_path, font_size)
    if cache_key not in _font_cache:
        _font_cache[cache_key] = pygame.font.Font(font_path, font_size)
    return _font_cache[cache_key]


def draw_text(
    surface,
    text,
    color,
    x,
    y,
    centered=False,
    font=None,
    font_size=None,
    vcenter_rect=None,
):

    font_obj = _get_font(font, font_size)
    text_surface = font_obj.render(str(text), True, color)

    if vcenter_rect is not None:
        y = vcenter_rect.y + (vcenter_rect.height - text_surface.get_height()) // 2

    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))

    surface.blit(text_surface, text_rect)


# =0.34
def _get_border_radius(rect, border_radius):

    return int(min(rect.width, rect.height) * border_radius)


def _draw_rounded_rect(
    surface, color, rect, border_color=None, border_width=0, border_radius=0.34
):
   
    radius = _get_border_radius(rect, border_radius)

    if color:
        bg_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surface,
            color,
            pygame.Rect(0, 0, rect.width, rect.height),
            border_radius=radius,
        )
        surface.blit(bg_surface, rect.topleft)

    if border_color and border_width > 0:
        pygame.draw.rect(
            surface, border_color, rect, width=border_width, border_radius=radius
        )


def _draw_text_with_clipping(
    surface, text, rect, color, font_size=27, padding=15, is_password=False
):
    """Szöveg rajzolása clipping-gel"""
    display_text = "*" * len(text) if is_password else text

    clip_rect = pygame.Rect(
        rect.x + padding, rect.y, rect.width - 2 * padding, rect.height
    )
    surface.set_clip(clip_rect)

    draw_text(
        surface,
        display_text,
        color,
        rect.centerx,
        rect.centery,
        centered=True,
        font="thin",
        font_size=font_size,
    )

    surface.set_clip(None)

    font = _get_font("thin", font_size)
    text_surface = font.render(display_text, True, color)
    text_x = rect.centerx - text_surface.get_width() // 2
    text_y = rect.y + (rect.height - text_surface.get_height()) // 2

    return text_surface, text_x, text_y


def _draw_cursor(
    surface,
    rect,
    text_surface,
    text_x,
    text_y,
    is_active,
    cursor_visible,
    padding=15,
    cursor_color=WHITE,
):
    """Kurzor rajzolása"""
    if not (is_active and cursor_visible):
        return

    cursor_x = text_x + text_surface.get_width()

    if rect.x + padding <= cursor_x <= rect.x + rect.width - padding:
        pygame.draw.line(
            surface,
            cursor_color,
            (cursor_x, text_y),
            (cursor_x, text_y + text_surface.get_height()),
            2,
        )


def draw_input_box(
    surface,
    rect,
    text,
    is_active=False,
    is_password=False,
    cursor_visible=True,
    background_color=None,
    border_color=DARK_GREEN,
    border_radius=0.34,
    active_background_color=None,
    text_color=WHITE,
    cursor_color=WHITE,
    font_size=27,
    padding=15,
    placeholder=None,
    placeholder_color=(128, 128, 128),
):
    bg_color = (
        active_background_color
        if (is_active and active_background_color)
        else background_color
    )

    _draw_rounded_rect(surface, bg_color, rect, border_color, 2, border_radius)

    if text:
        text_surface, text_x, text_y = _draw_text_with_clipping(
            surface, text, rect, text_color, font_size, padding, is_password
        )
        _draw_cursor(
            surface,
            rect,
            text_surface,
            text_x,
            text_y,
            is_active,
            cursor_visible,
            padding,
            cursor_color,
        )
    elif placeholder:
        _draw_text_with_clipping(
            surface, placeholder, rect, placeholder_color, font_size, padding
        )
    elif is_active and cursor_visible:
        font = _get_font("thin", font_size)
        empty_surface = font.render("", True, text_color)
        cursor_x = rect.x + rect.width // 2
        cursor_y = rect.y + (rect.height - empty_surface.get_height()) // 2
        pygame.draw.line(
            surface,
            cursor_color,
            (cursor_x, cursor_y),
            (cursor_x, cursor_y + empty_surface.get_height()),
            2,
        )


def validate_text_input(
    current_text,
    new_char,
    rect,
    max_length,
    is_password=False,
    font_size=27,
    padding=15,
):
    """Szöveg input validáció"""
    if len(current_text) >= max_length:
        return False

    test_text = current_text + new_char
    display_text = "*" * len(test_text) if is_password else test_text

    font = _get_font("thin", font_size)
    test_surface = font.render(display_text, True, WHITE)

    return test_surface.get_width() <= rect.width - 2 * padding - 10


def _scale_image_to_cover(image, target_width, target_height):
    """Kép méretezése hogy teljesen fedje a célt"""
    img_width, img_height = image.get_size()
    scale = max(target_width / img_width, target_height / img_height)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    return pygame.transform.scale(image, (new_width, new_height))


def load_background(
    screen_width, screen_height, surface, type: str = "light_background"
):
    """Háttér betöltése és méretezése"""
    bg_path = os.path.join(
        "csotanypoker", "client", "images", "ui-elements", "backgrounds", f"{type}.png"
    )
    bg_image = pygame.image.load(bg_path).convert()

    scaled_bg = _scale_image_to_cover(bg_image, screen_width, screen_height)
    rect = scaled_bg.get_rect(center=(screen_width // 2, screen_height // 2))
    surface.blit(scaled_bg, rect)


def load_image(name, type, scale_ratio=None, size=None):
    """Kép betöltése típus alapján"""
    path_mapping = {
        "logo": ("logos", f"{name}_logo.png"),
        "card": ("cards", f"{name}.png"),
        "button": ("ui-elements/buttons", f"{name}.png"),
    }

    if type not in path_mapping:
        raise ValueError(f"Ismeretlen kép típus: {type}")

    folder, filename = path_mapping[type]
    path = os.path.join("csotanypoker", "client", "images", folder, filename)
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


def _get_button_color(
    is_hovered,
    is_pressed,
    normal_color=DARK_GREEN,
    hover_color=MIDDLE_GREEN,
    pressed_color=LIGHT_GREEN_TRANSPARENT,
):
    """Gomb színének meghatározása állapot alapján"""
    if is_pressed:
        return pressed_color
    elif is_hovered:
        return hover_color
    else:
        return normal_color


def draw_button(
    surface,
    rect,
    text,
    text_color=WHITE,
    background_color=DARK_GREEN,
    border_color=DARK_GREEN,
    font_size=30,
    font_type="bold",
    border_width=5,
    is_hovered=False,
    is_pressed=False,
    hover_color=MIDDLE_GREEN,
    pressed_color=LIGHT_GREEN_TRANSPARENT,
):
    """
    Gomb rajzolása lekerekített sarkokkal

    Args:
        surface: A felület, amire rajzolunk
        rect: A gomb téglalap koordinátái
        text: A gomb szövege
        text_color: A szöveg színe
        background_color: A normál háttérszín
        border_color: A keret színe
        font_size: A betűméret
        font_type: A betűtípus ("regular", "bold", "thin")
        border_width: A keret vastagsága
        is_hovered: Van-e hover állapot
        is_pressed: Van-e nyomva állapot
        hover_color: A hover állapot színe
        pressed_color: A nyomva állapot színe
    """

    current_color = _get_button_color(
        is_hovered, is_pressed, background_color, hover_color, pressed_color
    )

    _draw_rounded_rect(surface, current_color, rect, border_color, border_width)

    draw_text(
        surface,
        text,
        text_color,
        rect.centerx,
        rect.centery,
        centered=True,
        font=font_type,
        font_size=font_size,
    )


def draw_image(surface, image, x, y, size=None, centered=False):
    """Kép rajzolása"""
    if size:
        image = pygame.transform.scale(image, size)

    rect = image.get_rect()
    if centered:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)
