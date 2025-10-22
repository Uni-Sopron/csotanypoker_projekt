import pygame
from typing import Union

from csotanypoker.client.drawing_helpers.constans import (
    FONT_SIZE_DEFAULT,
    FONT_PATH_REGULAR,
    FONT_PATH_BOLD,
    FONT_PATH_THIN,
)
from csotanypoker.client.utils.path_helper import resource_path

_font_cache = {}


_FONT_PATHS = {
    "regular": FONT_PATH_REGULAR,
    "bold": FONT_PATH_BOLD,
    "thin": FONT_PATH_THIN,
}


def _get_font(
    font_type: Union[str, pygame.font.Font], font_size: int = None
) -> pygame.font.Font:
    """Get font from cache or create new one"""
    font_size = font_size or FONT_SIZE_DEFAULT

    if isinstance(font_type, pygame.font.Font):
        if font_size == FONT_SIZE_DEFAULT:
            return font_type
        font_path = getattr(font_type, "_name", FONT_PATH_REGULAR)
    else:
        font_path = _FONT_PATHS.get(str(font_type).lower(), FONT_PATH_REGULAR)

    cache_key = (font_path, font_size)
    if cache_key not in _font_cache:
        _font_cache[cache_key] = pygame.font.Font(resource_path(font_path), font_size)
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
    """Draw text on surface"""
    font_obj = _get_font(font, font_size)
    text_surface = font_obj.render(str(text), True, color)

    if vcenter_rect:
        y = vcenter_rect.y + (vcenter_rect.height - text_surface.get_height()) // 2

    if centered:
        rect = text_surface.get_rect(center=(x, y))
    else:
        rect = text_surface.get_rect(topleft=(x, y))
    surface.blit(text_surface, rect)


def _render_text_surface(text, font_size, color, is_password=False):
    """Helper to render text surface"""
    display_text = "*" * len(text) if is_password else text
    font = _get_font("thin", font_size)
    return font.render(display_text, True, color)


def draw_text_with_clipping(
    surface, text, rect, color, font_size=27, padding=15, is_password=False
):
    """Draw text with clipping"""
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

    text_surface = _render_text_surface(text, font_size, color, is_password)
    text_x = rect.centerx - text_surface.get_width() // 2
    text_y = rect.y + (rect.height - text_surface.get_height()) // 2

    return text_surface, text_x, text_y


def wrap_text(text, max_length=30):
    """Szöveg tördelése a megadott hosszúságnál"""
    if len(text) <= max_length:
        return [text]

    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}" if current_line else word

        if len(test_line) <= max_length:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                lines.append(word[:max_length])
                current_line = word[max_length:]

    if current_line:
        lines.append(current_line)

    return lines


def wrap_text_for_popup(text, max_width, font_size):
    """Szöveg tördelése popup ablakhoz"""
    font = _get_font("regular", font_size)
    lines = []

    for paragraph in text.strip().split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}" if current_line else word

            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    while word:
                        for i in range(len(word), 0, -1):
                            test_word = word[:i] + ("-" if i < len(word) else "")
                            if font.size(test_word)[0] <= max_width:
                                lines.append(test_word)
                                word = word[i:]
                                break
                        else:
                            lines.append(word[:1])
                            word = word[1:]

        if current_line:
            lines.append(current_line)

    return lines


def format_username_for_display(username: str, max_length: int = 10):
    """
    Format username for display, returns list of lines if wrapping needed
    """
    if len(username) <= max_length:
        return [username]

    return wrap_text(username, max_length)
