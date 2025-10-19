import pygame
from typing import Tuple
from csotanypoker.client.drawing_helpers.drawing_helpers import (
    _draw_rounded_rect,
    draw_sound_volume,
    draw_text,
    draw_button,
)
from csotanypoker.client.drawing_helpers.constans import (
    LEGVILAGOS_ZOLD,
    MIDDLE_GREEN,
    DARK_GREEN,
    WHITE,
)


class MusicMenu:
    def __init__(self):
        self.visible = False
        self.music_volume = 0
        self.sound_effects_volume = 0
        self.dragging_music = False
        self.dragging_sound = False
        self.menu_rect = None

        self.save_button_rect = None
        self.music_slider_rect = None
        self.sound_slider_rect = None

    def show(self, screen_width: int, screen_height: int, music_manager=None):
        self.visible = True

        if music_manager:
            current_music_vol = music_manager.music_volume
            self.music_volume = (
                int((current_music_vol / 0.1) * 10) if current_music_vol > 0 else 0
            )

            current_sound_vol = music_manager.sound_effects_volume
            self.sound_effects_volume = int(current_sound_vol * 10)

        menu_width = int(screen_width * 0.7)
        menu_height = int(screen_height * 0.7)
        menu_x = (screen_width - menu_width) // 2
        menu_y = (screen_height - menu_height) // 2

        self.menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

        save_width = 250
        save_height = 80
        self.save_button_rect = pygame.Rect(
            menu_x + (menu_width - save_width) // 2,
            menu_y + menu_height - 100,
            save_width,
            save_height,
        )

        slider_width = int(menu_width * 0.6)
        slider_height = 20
        slider_x = menu_x + (menu_width - slider_width) // 2

        self.music_slider_rect = pygame.Rect(
            slider_x, menu_y + 150, slider_width, slider_height
        )

        self.sound_slider_rect = pygame.Rect(
            slider_x, menu_y + 280, slider_width, slider_height
        )

    def hide(self):
        self.visible = False

    def draw(self, surface: pygame.Surface):
        if not self.visible or not self.menu_rect:
            return

        _draw_rounded_rect(
            surface, LEGVILAGOS_ZOLD, self.menu_rect, MIDDLE_GREEN, 5, 0.05
        )

        draw_text(
            surface,
            "Hangerő",
            MIDDLE_GREEN,
            self.menu_rect.centerx,
            self.menu_rect.y + 60,
            centered=True,
            font="bold",
            font_size=55,
        )

        self._draw_music_section(surface)

        self._draw_sound_section(surface)

        draw_button(
            surface,
            self.save_button_rect,
            "Mentés",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=3,
        )

    def _draw_music_section(self, surface: pygame.Surface):
        icon_x = self.music_slider_rect.x - 80
        icon_y = self.music_slider_rect.centery

        draw_sound_volume(
            surface,
            icon_x,
            icon_y,
            "music",
        )

        pygame.draw.rect(
            surface, MIDDLE_GREEN, self.music_slider_rect, border_radius=10
        )

        handle_x = (
            self.music_slider_rect.x
            + (self.music_volume / 10) * self.music_slider_rect.width
        )
        handle_rect = pygame.Rect(handle_x - 12, self.music_slider_rect.y - 5, 24, 30)
        pygame.draw.ellipse(surface, DARK_GREEN, handle_rect)

        draw_text(
            surface,
            "0",
            MIDDLE_GREEN,
            self.music_slider_rect.x - 20,
            icon_y,
            centered=True,
            font_size=40,
        )
        draw_text(
            surface,
            "10",
            MIDDLE_GREEN,
            self.music_slider_rect.right + 20,
            icon_y,
            centered=True,
            font_size=40,
        )

    def _draw_sound_section(self, surface: pygame.Surface):
        icon_x = self.sound_slider_rect.x - 80
        icon_y = self.sound_slider_rect.centery

        draw_sound_volume(
            surface,
            icon_x,
            icon_y,
            "sound",
        )

        pygame.draw.rect(
            surface, MIDDLE_GREEN, self.sound_slider_rect, border_radius=10
        )

        handle_x = (
            self.sound_slider_rect.x
            + (self.sound_effects_volume / 10) * self.sound_slider_rect.width
        )
        handle_rect = pygame.Rect(handle_x - 12, self.sound_slider_rect.y - 5, 24, 30)
        pygame.draw.ellipse(surface, DARK_GREEN, handle_rect)

        draw_text(
            surface,
            "0",
            MIDDLE_GREEN,
            self.sound_slider_rect.x - 20,
            icon_y,
            centered=True,
            font_size=40,
        )
        draw_text(
            surface,
            "10",
            MIDDLE_GREEN,
            self.sound_slider_rect.right + 20,
            icon_y,
            centered=True,
            font_size=40,
        )

    def handle_mouse_click(self, pos: Tuple[int, int], music_manager) -> bool:
        if not self.visible:
            return False

        if self.save_button_rect and self.save_button_rect.collidepoint(pos):
            self._apply_settings(music_manager)
            self.hide()
            return True

        if self.music_slider_rect and self.music_slider_rect.collidepoint(pos):
            self.dragging_music = True
            self._update_music_volume(pos, music_manager)
            return True  

        if self.sound_slider_rect and self.sound_slider_rect.collidepoint(pos):
            self.dragging_sound = True
            self._update_sound_volume(pos, music_manager)
            return True 

        if self.menu_rect and self.menu_rect.collidepoint(pos):
            return False

        self.hide()
        return None




    def handle_mouse_release(self, pos: Tuple[int, int]):
        self.dragging_music = False
        self.dragging_sound = False

    def handle_mouse_motion(self, pos: Tuple[int, int], music_manager=None):
        if self.dragging_music and music_manager:
            self._update_music_volume(pos, music_manager)
        elif self.dragging_sound and music_manager:
            self._update_sound_volume(pos, music_manager)
    def _update_music_volume(self, pos: Tuple[int, int], music_manager=None):
        if not self.music_slider_rect:
            return

        relative_x = pos[0] - self.music_slider_rect.x
        relative_x = max(0, min(relative_x, self.music_slider_rect.width))

        ratio = relative_x / self.music_slider_rect.width
        new_volume = min(10, round(ratio * 10))

        if new_volume != self.music_volume:
            self.music_volume = new_volume

            if music_manager:
                music_vol = (self.music_volume / 10) * 0.1
                music_manager.set_music_volume(music_vol)

    def _update_sound_volume(self, pos: Tuple[int, int], music_manager=None):
        if not self.sound_slider_rect:
            return

        relative_x = pos[0] - self.sound_slider_rect.x
        relative_x = max(0, min(relative_x, self.sound_slider_rect.width))

        ratio = relative_x / self.sound_slider_rect.width
        new_volume = min(10, round(ratio * 10))

        if new_volume != self.sound_effects_volume:
            self.sound_effects_volume = new_volume

            if music_manager:
                sound_vol = self.sound_effects_volume / 10
                music_manager.set_sound_effects_volume(sound_vol)
                music_manager.button_click_sound()

    def _apply_settings(self, music_manager):
        music_vol = (self.music_volume / 10) * 0.1
        music_manager.set_music_volume(music_vol)

        sound_vol = self.sound_effects_volume / 10
        music_manager.set_sound_effects_volume(sound_vol)
