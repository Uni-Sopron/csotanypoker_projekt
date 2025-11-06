import pygame
from typing import Tuple
from csotanypoker.client.drawing_helpers.drawing_helpers import (
    _draw_rounded_rect,
    draw_text,
    draw_button,
)
from csotanypoker.client.drawing_helpers.constans import (
    LEGVILAGOS_ZOLD,
    MIDDLE_GREEN,
    DARK_GREEN,
    WHITE,
    CREDITS_TEXT,
)


class CreditsMenu:
    def __init__(self):
        self.visible = False
        self.menu_rect = None
        self.close_button_rect = None
        self.content_rect = None

        self.dragging = False
        self.drag_start_y = 0
        self.drag_start_offset = 0

    def show(self, screen_width: int, screen_height: int):
        self.visible = True

        menu_width = int(screen_width * 0.9)
        menu_height = int(screen_height * 0.95)
        menu_x = (screen_width - menu_width) // 2
        menu_y = (screen_height - menu_height) // 2

        self.menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

        close_width = 50
        close_height = 50
        self.close_button_rect = pygame.Rect(
            menu_x + menu_width - close_width - 20,
            menu_y + 20,
            close_width,
            close_height,
        )

        content_padding = 40
        self.content_rect = pygame.Rect(
            menu_x + content_padding,
            menu_y + 30,
            menu_width - (content_padding * 2),
            menu_height - 220,
        )

    def hide(self):
        self.visible = False

    def draw(self, surface: pygame.Surface):
        if not self.visible or not self.menu_rect:
            return

        _draw_rounded_rect(
            surface, LEGVILAGOS_ZOLD, self.menu_rect, MIDDLE_GREEN, 5, 0.05
        )

        if self.content_rect:
            original_clip = surface.get_clip()
            surface.set_clip(self.content_rect)

            content_y = self.content_rect.y
            line_height = 35
            y_pos = content_y

            draw_text(
                surface,
                "Eredeti játék neve: Csótány Póker",
                DARK_GREEN,
                self.content_rect.x + 20,
                y_pos,
                centered=False,
                font="bold",
                font_size=28,
            )
            y_pos += line_height

            draw_text(
                surface,
                "Készítője: Jacques Zeimet",
                MIDDLE_GREEN,
                self.content_rect.x + 40,
                y_pos,
                centered=False,
                font_size=28,
            )

            y_pos += line_height

            draw_text(
                surface,
                "Játékfejlesztés és grafikai elemek: Skriba Izabella",
                DARK_GREEN,
                self.content_rect.x + 20,
                y_pos,
                centered=False,
                font="bold",
                font_size=28,
            )
            y_pos += line_height

            draw_text(
                surface,
                "Felhasznált audió anyagok és betűtípus:",
                DARK_GREEN,
                self.content_rect.x + 20,
                y_pos,
                centered=False,
                font="bold",
                font_size=28,
            )
            y_pos += line_height + 10

        for line in CREDITS_TEXT.strip().split("\n"):
            draw_text(
                surface,
                line.strip(),
                MIDDLE_GREEN,
                self.content_rect.x + 40,
                y_pos,
                centered=False,
                font="regular",
                font_size=20,
            )
            y_pos += line_height

            surface.set_clip(original_clip)

        draw_button(
            surface,
            self.close_button_rect,
            "X",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=28,
            font_type="bold",
            border_width=3,
        )

    def handle_mouse_click(self, pos: Tuple[int, int]) -> bool:
        if not self.visible:
            return False
        if self.close_button_rect and self.close_button_rect.collidepoint(pos):
            self.hide()
            return True
        if self.menu_rect and self.menu_rect.collidepoint(pos):
            return False

        self.hide()
        return True
