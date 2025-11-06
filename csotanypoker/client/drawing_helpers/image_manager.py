import os
import pygame
from typing import Dict
from csotanypoker.client.utils.path_helper import resource_path
_image_cache: Dict[str, pygame.Surface] = {}
_scaled_image_cache: Dict[tuple, pygame.Surface] = {}
from csotanypoker.models.animal import Animal  


def preload_all_images():
    for animal in Animal:
        _get_cached_image(animal, "logo")

        _get_cached_scaled_image(animal, "logo", (50, 50))
        _get_cached_scaled_image(animal, "logo", (58, 58))
        _get_cached_scaled_image(animal, "logo", (64, 64))  # hover
        _get_cached_scaled_image(animal, "logo", (70, 70))  # active

    for animal in Animal:
        _get_cached_image(animal, "card")

        card_size = (int(650 * 0.17), int(1000 * 0.17))
        _get_cached_scaled_image(animal, "card", card_size)

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
        path = resource_path(os.path.join("csotanypoker", "client", "images", folder, filename))

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


def load_image(name: str, image_type=None, type=None, scale_ratio=None, size=None):
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


def load_background(
    screen_width, screen_height, surface, type: str = "light_background"
):
    bg_image = _get_cached_image(type, "background")

    scaled_bg = _scale_image_to_cover(bg_image, screen_width, screen_height)
    rect = scaled_bg.get_rect(center=(screen_width // 2, screen_height // 2))
    surface.blit(scaled_bg, rect)


def _scale_image_to_cover(image, target_width, target_height):
    """Scale image to cover target area completely"""
    img_width, img_height = image.get_size()
    scale = max(target_width / img_width, target_height / img_height)
    new_size = (int(img_width * scale), int(img_height * scale))
    return pygame.transform.scale(image, new_size)




