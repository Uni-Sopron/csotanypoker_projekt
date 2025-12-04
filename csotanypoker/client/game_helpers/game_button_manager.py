import pygame
from csotanypoker.client.drawing_helpers.drawing_helpers import (
    check_logout_button_interaction,
    check_rules_button_interaction,
    create_logout_button_rect,
    create_rules_button_rect,
)


class GameButtonManager:
    def __init__(self, screen):
        self.screen = screen

    def update_button_rects(self):
        self.screen.logout_button = create_logout_button_rect(self.screen.client.height)
        self.screen.rules_button = create_rules_button_rect(
            self.screen.client.width, self.screen.client.height
        )
        self.screen.leave_button = pygame.Rect(
            self.screen.logout_button.x, self.screen.logout_button.y - 90, 200, 75
        )
        self.screen.pass_button = pygame.Rect(
            self.screen.client.width // 2 - 50,
            self.screen.client.height // 2 + 150,
            100,
            35,
        )

    def update_button_states(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.screen.hovered_elements.clear()
        if not mouse_pressed:
            self.screen.pressed_elements.clear()

        is_logout_hovered, is_logout_pressed = check_logout_button_interaction(
            mouse_pos, mouse_pressed, self.screen.logout_button
        )
        if is_logout_hovered:
            self.screen.hovered_elements.add("logout")
        if is_logout_pressed:
            self.screen.pressed_elements.add("logout")

        self.screen.show_rules = check_rules_button_interaction(
            mouse_pos, self.screen.rules_button
        )
        if self.screen.leave_button.collidepoint(mouse_pos):
            self.screen.hovered_elements.add("leave")
            if mouse_pressed:
                self.screen.pressed_elements.add("leave")

        if (
            hasattr(self.screen, "oke_button")
            and self.screen.oke_button is not None
            and self.screen.oke_button.collidepoint(mouse_pos)
        ):
            self.screen.hovered_elements.add("ok")
            if mouse_pressed:
                self.screen.pressed_elements.add("ok")

        if (
            hasattr(self.screen, "pass_button")
            and self.screen.pass_button is not None
            and self.screen.pass_button.collidepoint(mouse_pos)
        ):
            self.screen.hovered_elements.add("pass")
            if mouse_pressed:
                self.screen.pressed_elements.add("pass")

        if (
            hasattr(self.screen, "cross_rect")
            and self.screen.cross_rect is not None
            and self.screen.cross_rect.collidepoint(mouse_pos)
        ):
            self.screen.hovered_elements.add("cross")
            if mouse_pressed:
                self.screen.pressed_elements.add("cross")

        if (
            hasattr(self.screen, "checkmark_rect")
            and self.screen.checkmark_rect is not None
            and self.screen.checkmark_rect.collidepoint(mouse_pos)
        ):
            self.screen.hovered_elements.add("checkmark")
            if mouse_pressed:
                self.screen.pressed_elements.add("checkmark")
