import pygame
from typing import Union

from csotanypoker.client.drawing_helpers.constans import (
    FONT_SIZE_DEFAULT,
    FONT_PATH_REGULAR,
    FONT_PATH_BOLD,
    FONT_PATH_THIN,
    WHITE,
)
from csotanypoker.client.utils.path_helper import resource_path

_font_cache = {}


_FONT_PATHS = {
    "regular": FONT_PATH_REGULAR,
    "bold": FONT_PATH_BOLD,
    "thin": FONT_PATH_THIN,
}


def handle_continuous_arrow_keys(input_state, keys, current_time, text_length):
    if not (input_state.left_held or input_state.right_held):
        return input_state.cursor_pos, False

    if current_time - input_state.last_arrow_time < input_state.arrow_repeat_delay:
        return input_state.cursor_pos, False

    changed = False
    new_pos = input_state.cursor_pos

    if input_state.left_held and input_state.cursor_pos > 0:
        new_pos = input_state.cursor_pos - 1
        changed = True
    elif input_state.right_held and input_state.cursor_pos < text_length:
        new_pos = input_state.cursor_pos + 1
        changed = True

    if changed:
        input_state.last_arrow_time = current_time

    return new_pos, changed


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


def draw_text_with_clipping_and_cursor(
    surface,
    text,
    rect,
    color,
    font_size=27,
    padding=15,
    is_password=False,
    cursor_pos=None,
    text_align="center",
):
    display_text = "*" * len(text) if is_password else text

    clip_rect = pygame.Rect(
        rect.x + padding, rect.y, rect.width - 2 * padding, rect.height
    )

    text_surface = _render_text_surface(text, font_size, color, is_password)
    text_width = text_surface.get_width()

    text_y = rect.y + (rect.height - text_surface.get_height()) // 2

    if text_align == "center":
        text_x = rect.x + (rect.width - text_width) // 2

        if cursor_pos is not None:
            text_before_cursor = text[:cursor_pos]
            cursor_surface = _render_text_surface(
                text_before_cursor, font_size, color, is_password
            )
            cursor_x_relative = cursor_surface.get_width()
            cursor_x = text_x + cursor_x_relative

            if cursor_x > rect.x + rect.width - padding:
                text_x = rect.x + rect.width - padding - cursor_x_relative - 10
            elif cursor_x < rect.x + padding:
                text_x = rect.x + padding
    else:
        text_x = rect.x + padding

        if cursor_pos is not None:
            text_before_cursor = text[:cursor_pos]
            cursor_surface = _render_text_surface(
                text_before_cursor, font_size, color, is_password
            )
            cursor_x_relative = cursor_surface.get_width()

            if cursor_x_relative > rect.width - 2 * padding - 10:
                text_x = rect.x + rect.width - padding - cursor_x_relative - 10
            elif cursor_pos == 0:
                text_x = rect.x + padding

    surface.set_clip(clip_rect)

    font = _get_font("thin", font_size)
    text_render = font.render(display_text, True, color)
    surface.blit(text_render, (text_x, text_y))

    surface.set_clip(None)

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


def handle_input_text_event(
    event,
    text,
    cursor_pos,
    max_length,
    rect,
    font_size=27,
    padding=15,
    is_password=False,
):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_BACKSPACE:
            if cursor_pos > 0:
                new_text = text[: cursor_pos - 1] + text[cursor_pos:]
                return new_text, cursor_pos - 1, True
            return text, cursor_pos, True

        elif event.key == pygame.K_DELETE:
            if cursor_pos < len(text):
                new_text = text[:cursor_pos] + text[cursor_pos + 1 :]
                return new_text, cursor_pos, True
            return text, cursor_pos, True

        elif event.key == pygame.K_LEFT:
            new_pos = max(0, cursor_pos - 1)
            return text, new_pos, True

        elif event.key == pygame.K_RIGHT:
            new_pos = min(len(text), cursor_pos + 1)
            return text, new_pos, True

        elif event.key == pygame.K_HOME:
            return text, 0, True

        elif event.key == pygame.K_END:
            return text, len(text), True

        elif len(event.unicode) == 1 and event.unicode.isprintable():
            if len(text) < max_length:
                test_text = text[:cursor_pos] + event.unicode + text[cursor_pos:]
                test_surface = _render_text_surface(
                    test_text, font_size, WHITE, is_password
                )

                if test_surface.get_width() <= rect.width - 2 * padding - 10:
                    new_text = text[:cursor_pos] + event.unicode + text[cursor_pos:]
                    return new_text, cursor_pos + 1, True
            return text, cursor_pos, True

    return text, cursor_pos, False


def handle_continuous_backspace(input_state, text, current_time):
    if not input_state.backspace_held:
        return text, input_state.cursor_pos, False

    if (
        current_time - input_state.last_backspace_time
        < input_state.backspace_repeat_delay
    ):
        return text, input_state.cursor_pos, False

    if input_state.cursor_pos > 0:
        new_text = text[: input_state.cursor_pos - 1] + text[input_state.cursor_pos :]
        input_state.cursor_pos -= 1
        input_state.last_backspace_time = current_time
        return new_text, input_state.cursor_pos, True

    return text, input_state.cursor_pos, False


def handle_mouse_click_in_input(
    pos, rect, text, font_size=27, padding=15, is_password=False
):
    if not rect.collidepoint(pos):
        return None

    relative_x = pos[0] - (rect.x + padding)

    if relative_x <= 0:
        return 0
    best_pos = len(text)
    best_distance = float("inf")

    for i in range(len(text) + 1):
        text_before = text[:i]
        surface = _render_text_surface(text_before, font_size, WHITE, is_password)
        width = surface.get_width()
        distance = abs(width - relative_x)

        if distance < best_distance:
            best_distance = distance
            best_pos = i

    return best_pos
