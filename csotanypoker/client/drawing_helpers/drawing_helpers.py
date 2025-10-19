import pygame
from csotanypoker.client.drawing_helpers.constans import (
    DARK_GREEN_TRANSPARENT,
    MIDDLE_GREEN_TRANSPARENT_70,
    WHITE,
    DARK_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    MIDDLE_GREEN,
    LIGHT_GREEN,
    LEGVILAGOS_ZOLD,
)
from csotanypoker.client.drawing_helpers.image_manager import load_image
from csotanypoker.client.drawing_helpers.text_manager import (
    draw_text_with_clipping,
    _render_text_surface,
    wrap_text_for_popup,
    draw_text,
)


def draw_sound_volume(surface, x, y, type):
    volume_image = load_image(type, "button", size=(60, 60))

    draw_image(surface, volume_image, x, y, centered=True)


def create_volume_button_rect(x, y):
    return pygame.Rect(x - 25, y - 25, 50, 50)


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
        text_surface, text_x, text_y = draw_text_with_clipping(
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
        draw_text_with_clipping(
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

    lines = wrap_text_for_popup(rules_text, available_width, 30)

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
        network_client.logout()
        return True
    return False





def create_standard_input_rect(x, y, width=230, height=50):
    """Standard input mező rect létrehozása"""
    return pygame.Rect(x, y, width, height)


def draw_input_field(
    surface,
    rect,
    text,
    is_active,
    placeholder="",
    is_password=False,
    text_color=WHITE,
    background_color=LIGHT_GREEN_TRANSPARENT,
    border_color=None,
    placeholder_color=MIDDLE_GREEN,
    cursor_color=WHITE,
    font_size=23,
):
    """Egységes input mező rajzolása"""
    draw_input_box(
        surface=surface,
        rect=rect,
        text=text,
        text_color=text_color,
        background_color=background_color,
        border_color=border_color,
        border_radius=0.50,
        font_size=font_size,
        is_active=is_active,
        cursor_color=cursor_color,
        placeholder=placeholder,
        placeholder_color=placeholder_color,
        is_password=is_password,
    )


def draw_standard_button(
    surface,
    rect,
    text,
    is_enabled=True,
    is_hovered=False,
    is_pressed=False,
    font_size=25,
):
    """Standard gomb rajzolása engedélyezett/letiltott állapottal"""
    if is_enabled:
        bg_color = MIDDLE_GREEN
        hover_color = MIDDLE_GREEN_TRANSPARENT_70
        pressed_color = LIGHT_GREEN
    else:
        bg_color = DARK_GREEN_TRANSPARENT
        hover_color = DARK_GREEN_TRANSPARENT
        pressed_color = DARK_GREEN_TRANSPARENT

    draw_button(
        surface=surface,
        rect=rect,
        text=text,
        text_color=WHITE,
        background_color=bg_color,
        border_color=DARK_GREEN,
        font_size=font_size,
        font_type="bold",
        border_width=3,
        is_hovered=is_hovered and is_enabled,
        is_pressed=is_pressed and is_enabled,
        hover_color=hover_color,
        pressed_color=pressed_color,
    )


def draw_icon_button(surface, image_name, x, y, size=(35, 35), centered=True):
    """Ikon gomb rajzolása és rect visszaadása"""
    image = load_image(image_name, "button", size=size)
    if centered:
        button_rect = pygame.Rect(x - size[0] // 2, y - size[1] // 2, size[0], size[1])
    else:
        button_rect = pygame.Rect(x, y, size[0], size[1])
    
    draw_image(surface, image, x, y, centered=centered)
    return button_rect


def draw_scrollbar(surface, scroll_bar_rect, scroll_offset, total_items, visible_items):
    """Scrollbar rajzolása"""
    if not scroll_bar_rect or total_items <= visible_items:
        return

    _draw_rounded_rect(surface, LIGHT_GREEN_TRANSPARENT, scroll_bar_rect)

    visible_ratio = visible_items / total_items
    scroll_ratio = scroll_offset / (total_items - visible_items)

    thumb_height = max(20, int(scroll_bar_rect.height * visible_ratio))
    thumb_y = scroll_bar_rect.y + int(
        (scroll_bar_rect.height - thumb_height) * scroll_ratio
    )

    thumb_rect = pygame.Rect(
        scroll_bar_rect.x + 2,
        thumb_y,
        scroll_bar_rect.width - 4,
        thumb_height,
    )
    _draw_rounded_rect(surface, MIDDLE_GREEN, thumb_rect)
    
    return thumb_rect