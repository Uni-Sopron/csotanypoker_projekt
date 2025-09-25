import os
import pygame
from typing import Union, Dict

from csotanypoker.client.constans import (
    FONT_SIZE_DEFAULT,
    FONT_PATH_REGULAR,
    FONT_PATH_BOLD,
    FONT_PATH_THIN,
    WHITE,
    DARK_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    MIDDLE_GREEN,
    LIGHT_GREEN,
    LEGVILAGOS_ZOLD,
)
from csotanypoker.models.user import AI_NAMES


def this_is_ai_name(name: str) -> str:
    for ai_name in AI_NAMES:
        if name.startswith(ai_name):
            return ai_name

    return name


_font_cache = {}

_image_cache: Dict[str, pygame.Surface] = {}
_scaled_image_cache: Dict[tuple, pygame.Surface] = {}

_FONT_PATHS = {
    "regular": FONT_PATH_REGULAR,
    "bold": FONT_PATH_BOLD,
    "thin": FONT_PATH_THIN,
}


def preload_all_images():
    from csotanypoker.models.animal import Animal

    for animal in Animal:
        _get_cached_image(animal.value, "logo")

        _get_cached_scaled_image(animal.value, "logo", (50, 50))
        _get_cached_scaled_image(animal.value, "logo", (58, 58))
        _get_cached_scaled_image(animal.value, "logo", (64, 64))  # hover
        _get_cached_scaled_image(animal.value, "logo", (70, 70))  # active

    for animal in Animal:
        _get_cached_image(animal.value, "card")

        card_size = (int(650 * 0.17), int(1000 * 0.17))
        _get_cached_scaled_image(animal.value, "card", card_size)

    ui_elements = [
        "question_mark",
        "search_symbol",
        "padlock",
        "unlock_padlock",
        "padlock_transparent",
        "fel_le_nyilak",
    ]
    for element in ui_elements:
        _get_cached_image(element, "button")

        _get_cached_scaled_image(element, "button", (35, 35))
        _get_cached_scaled_image(element, "button", (40, 40))
        _get_cached_scaled_image(element, "button", (50, 50))

    background_types = [
        "light_background",
        "background",
    ]
    for bg_type in background_types:
        _get_cached_image(bg_type, "background")


def _get_cached_image(name: str, image_type: str) -> pygame.Surface:
    """Alapkép betöltése cache-ből vagy fájlból"""
    cache_key = f"{image_type}:{name}"

    if cache_key not in _image_cache:
        path_mapping = {
            "logo": ("logos", f"{name}_logo.png"),
            "card": ("cards", f"{name}.png"),
            "button": ("ui-elements/buttons", f"{name}.png"),
            "background": ("ui-elements/backgrounds", f"{name}.png"),
        }

        if image_type not in path_mapping:
            raise ValueError(f"Unknown image type: {image_type}")

        folder, filename = path_mapping[image_type]
        path = os.path.join("csotanypoker", "client", "images", folder, filename)

        try:
            image = pygame.image.load(path).convert_alpha()
            _image_cache[cache_key] = image
        except pygame.error as e:
            _image_cache[cache_key] = pygame.Surface((50, 50), pygame.SRCALPHA)

    return _image_cache[cache_key]


def _get_cached_scaled_image(name: str, image_type: str, size: tuple) -> pygame.Surface:
    scale_key = (image_type, name, size)

    if scale_key not in _scaled_image_cache:
        base_image = _get_cached_image(name, image_type)
        scaled_image = pygame.transform.scale(base_image, size)
        _scaled_image_cache[scale_key] = scaled_image

    return _scaled_image_cache[scale_key]


def load_image(name, image_type=None, type=None, scale_ratio=None, size=None):
    if type is not None and image_type is None:
        image_type = type

    if image_type is None:
        raise ValueError("image_type vagy type paramétert meg kell adni!")

    if not scale_ratio and not size:
        return _get_cached_image(name, image_type)

    if scale_ratio and not size:
        base_image = _get_cached_image(name, image_type)
        original_size = base_image.get_size()
        size = (
            int(original_size[0] * scale_ratio),
            int(original_size[1] * scale_ratio),
        )

    if size:
        return _get_cached_scaled_image(name, image_type, size)

    return _get_cached_image(name, image_type)


def clear_image_cache():
    global _image_cache, _scaled_image_cache
    _image_cache.clear()
    _scaled_image_cache.clear()
    print("Kép cache törölve")


def load_background(
    screen_width, screen_height, surface, type: str = "light_background"
):
    bg_image = _get_cached_image(type, "background")

    scaled_bg = _scale_image_to_cover(bg_image, screen_width, screen_height)
    rect = scaled_bg.get_rect(center=(screen_width // 2, screen_height // 2))
    surface.blit(scaled_bg, rect)


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
        _font_cache[cache_key] = pygame.font.Font(font_path, font_size)
    return _font_cache[cache_key]





def draw_music_volume(surface, x, y, volume_level):
    volume_images = {
        0: "volume0",  
        1: "volume1",  
        2: "volume2", 
        3: "volume3",  
    }

    volume_image = load_image(volume_images[volume_level], "button", size=(50, 50))


    draw_image(surface, volume_image, x, y, centered=True)


def create_volume_button_rect(x, y):
    return pygame.Rect(x - 25, y - 25, 50, 50)


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


def _draw_rounded_rect(
    surface, color, rect, border_color=None, border_width=0, border_radius=0.27
):
    """Draw rounded rectangle with optional border"""
    radius = int(min(rect.width, rect.height) * border_radius)

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


def _render_text_surface(text, font_size, color, is_password=False):
    """Helper to render text surface"""
    display_text = "*" * len(text) if is_password else text
    font = _get_font("thin", font_size)
    return font.render(display_text, True, color)


def _draw_text_with_clipping(
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
    """Draw cursor if active and visible"""
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
    """Draw input box with text, cursor and placeholder"""
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
    else:
        text_surface = _render_text_surface("", font_size, text_color)
        text_x = rect.x + rect.width // 2
        text_y = rect.y + (rect.height - text_surface.get_height()) // 2

    if is_active:
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        _draw_cursor(
            surface,
            rect,
            text_surface,
            text_x,
            text_y,
            is_active,
            blink,
            padding,
            cursor_color,
        )

    elif not text and placeholder:
        _draw_text_with_clipping(
            surface, placeholder, rect, placeholder_color, font_size, padding
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
    """Validate text input for length and visual fit"""
    if len(current_text) >= max_length:
        return False

    test_text = current_text + new_char
    test_surface = _render_text_surface(test_text, font_size, WHITE, is_password)

    return test_surface.get_width() <= rect.width - 2 * padding - 10


def _scale_image_to_cover(image, target_width, target_height):
    """Scale image to cover target area completely"""
    img_width, img_height = image.get_size()
    scale = max(target_width / img_width, target_height / img_height)
    new_size = (int(img_width * scale), int(img_height * scale))
    return pygame.transform.scale(image, new_size)


def _get_button_color(is_hovered, is_pressed, normal_color, hover_color, pressed_color):
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
    """Draw button with rounded corners and state-based colors"""
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
    """Draw image on surface"""
    if size:
        image = pygame.transform.scale(image, size)

    if centered:
        rect = image.get_rect(center=(x, y))
    else:
        rect = image.get_rect(topleft=(x, y))
    surface.blit(image, rect)


def draw_image_button(
    surface,
    image_name,
    image_type,
    x,
    y,
    base_size=(58, 58),
    border_radius=0.15,
    padding=10,
    is_hovered=False,
    is_active=False,
    hover_scale=1.1,
    active_scale=1.2,
    centered=True,
):
    scale = 1.0
    if is_active:
        scale = active_scale
    elif is_hovered:
        scale = hover_scale

    target_size = (int(base_size[0] * scale), int(base_size[1] * scale))

    scaled_image = load_image(image_name, image_type, size=target_size)

    button_width = target_size[0] + 2 * padding
    button_height = target_size[1] + 2 * padding

    if centered:
        button_x = x - button_width // 2
        button_y = y - button_height // 2
    else:
        button_x = x
        button_y = y

    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    _draw_rounded_rect(surface, None, button_rect, None, 0, border_radius)

    image_x = button_rect.centerx - scaled_image.get_width() // 2
    image_y = button_rect.centery - scaled_image.get_height() // 2
    surface.blit(scaled_image, (image_x, image_y))

    return button_rect


def create_logout_button_rect(screen_height):
    return pygame.Rect(20, screen_height - 95, 200, 75)


def create_rules_button_rect(screen_width, screen_height):
    return pygame.Rect(screen_width - 120, screen_height - 130, 100, 100)


def draw_logout_button(surface, rect, is_hovered=False, is_pressed=False):
    draw_button(
        surface=surface,
        rect=rect,
        text="Kijelentkezés",
        text_color=WHITE,
        background_color=DARK_GREEN,
        border_color=DARK_GREEN,
        font_size=28,
        font_type="bold",
        border_width=5,
        is_hovered=is_hovered,
        is_pressed=is_pressed,
        hover_color=MIDDLE_GREEN,
        pressed_color=LIGHT_GREEN,
    )


def draw_rules_button(surface, rect):
    rules_image = load_image(
        "question_mark",
        "button",
        size=(rect.width, rect.height),
    )
    draw_image(surface, rules_image, rect.x, rect.y)


def draw_rules_popup(surface, screen_width, screen_height, rules_text, max_players):
    """Szabályok popup rajzolása szöveg tördeléssel"""
    popup_width = int(screen_width * 0.8)
    popup_height = int(screen_height * 0.8)
    popup_x = (screen_width - popup_width) // 2
    popup_y = (screen_height - popup_height) // 2

    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    _draw_rounded_rect(surface, LEGVILAGOS_ZOLD, popup_rect, LIGHT_GREEN, 5, 0.05)

    rules_key = "2" if max_players == 2 else "3-6"
    title = f"Játékszabály ({rules_key} játékos)"

    margin = popup_height // 6
    title_y = popup_y + margin

    draw_text(
        surface,
        title,
        MIDDLE_GREEN,
        popup_x + popup_width // 2,
        title_y,
        centered=True,
        font="bold",
        font_size=40,
    )

    content_y = title_y + 80
    available_width = popup_width - 2 * margin

    lines = _wrap_text_for_popup(rules_text, available_width, 30)

    line_height = 40
    for i, line in enumerate(lines):
        if line.strip():
            y_pos = content_y + i * line_height
            if y_pos < popup_y + popup_height - margin:
                draw_text(
                    surface,
                    line,
                    MIDDLE_GREEN,
                    popup_x + margin,
                    y_pos,
                    centered=False,
                    font="regular",
                    font_size=30,
                )


def draw_multiline_text(
    surface,
    text_lines,
    color,
    x,
    y,
    centered=False,
    font=None,
    font_size=None,
    line_spacing=5,
):
    """
    Draw multiple lines of text with proper line spacing
    """
    if isinstance(text_lines, str):
        text_lines = [text_lines]

    font_obj = _get_font(font, font_size)

    total_height = (
        len(text_lines) * font_obj.get_height() + (len(text_lines) - 1) * line_spacing
    )

    for i, line in enumerate(text_lines):
        line_y = y + i * (font_obj.get_height() + line_spacing)
        if centered:
            line_y = y - total_height // 2 + i * (font_obj.get_height() + line_spacing)

        draw_text(
            surface,
            line,
            color,
            x,
            line_y,
            centered=centered,
            font=font,
            font_size=font_size,
        )


def format_username_for_display(username: str, max_length: int = 10):
    """
    Format username for display, returns list of lines if wrapping needed
    """
    if len(username) <= max_length:
        return [username]

    return wrap_text(username, max_length)


def _wrap_text_for_popup(text, max_width, font_size):
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


def check_logout_button_interaction(mouse_pos, mouse_pressed, logout_rect):
    """Check if logout button is being interacted with"""
    is_hovered = logout_rect.collidepoint(mouse_pos)
    is_pressed = is_hovered and mouse_pressed
    return is_hovered, is_pressed


def check_rules_button_interaction(mouse_pos, rules_rect):
    """Check if rules button is being hovered"""
    return rules_rect.collidepoint(mouse_pos)


def handle_logout_button_click(pos, logout_rect, network_client):
    """Handle logout button click and perform logout"""
    if logout_rect.collidepoint(pos):
        print("Logging out")
        network_client.logout()
        return True
    return False


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
