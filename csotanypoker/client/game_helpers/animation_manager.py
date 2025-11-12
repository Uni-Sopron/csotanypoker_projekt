class AnimationManager:
    def __init__(self):
        self._flip_progress = {}
        self._slide_animations = {}
        self._last_cards_count = {}
        self._card_placed_player = None

    def get_flip_data(self, card_key, target_card):
        if card_key not in self._flip_progress:
            self._flip_progress[card_key] = {
                "previous_card": None,
                "current_card": target_card,
                "progress": 1.0,
                "is_animating": False,
            }

        flip_data = self._flip_progress[card_key]

        if flip_data["current_card"] != target_card:
            if flip_data["current_card"] == "card_back" and target_card != "card_back":
                flip_data["progress"] = 0.0
                flip_data["previous_card"] = flip_data["current_card"]
                flip_data["current_card"] = target_card
                flip_data["is_animating"] = True
            else:
                flip_data["previous_card"] = flip_data["current_card"]
                flip_data["current_card"] = target_card
                flip_data["progress"] = 1.0
                flip_data["is_animating"] = False

        if flip_data["is_animating"]:
            if flip_data["progress"] < 1.0:
                flip_data["progress"] += 0.15
                if flip_data["progress"] >= 1.0:
                    flip_data["progress"] = 1.0
                    flip_data["is_animating"] = False

        return flip_data

    def check_card_placement(self, player_name, current_card_total):
        """Ellenőrzi, hogy nőtt-e a játékos előtti lapok száma"""
        key = f"placement_{player_name}"

        if key not in self._last_cards_count:
            self._last_cards_count[key] = current_card_total
            return False

        if current_card_total > self._last_cards_count[key]:
            self._last_cards_count[key] = current_card_total
            self._card_placed_player = player_name
            return True

        self._last_cards_count[key] = current_card_total
        return False

    def get_card_placed_player(self):
        """Visszaadja, hogy kinek lett lehelyezve a lap"""
        return self._card_placed_player

    def clear_card_placed_player(self):
        """Törli a lehelyezett lap játékos infót"""
        self._card_placed_player = None

    def get_slide_animation(self, card_key):
        """Csúszó animáció állapotának lekérése"""
        if card_key not in self._slide_animations:
            return None

        slide_data = self._slide_animations[card_key]

        if slide_data["is_animating"]:
            # Késleltetés kezelése (60 frame = 1 másodperc 60 FPS-nél)
            if slide_data.get("delay_frames", 0) > 0:
                slide_data["delay_frames"] -= 1
            else:
                slide_data["progress"] += 0.07
                if slide_data["progress"] >= 1.0:
                    slide_data["progress"] = 1.0
                    slide_data["is_animating"] = False

        # Lineáris interpoláció pozícióra
        current_x = (
            slide_data["start_pos"][0]
            + (slide_data["end_pos"][0] - slide_data["start_pos"][0])
            * slide_data["progress"]
        )
        current_y = (
            slide_data["start_pos"][1]
            + (slide_data["end_pos"][1] - slide_data["start_pos"][1])
            * slide_data["progress"]
        )

        # Méret interpoláció (1.0 -> 0.3)
        scale = 1.0 - (slide_data["progress"] * 0.7)

        return {
            "position": (current_x, current_y),
            "scale": scale,
            "is_animating": slide_data["is_animating"],
            "progress": slide_data["progress"],
        }

    def start_slide_animation(self, card_key, start_pos, end_pos):
        """Új csúszó animáció indítása"""
        self._slide_animations[card_key] = {
            "start_pos": start_pos,
            "end_pos": end_pos,
            "progress": 0.0,
            "is_animating": True,
            "delay_frames": 50,  # 30 frame = 0.5 másodperc (60 FPS)
        }

    def is_slide_animating(self, card_key):
        """Ellenőrzi, hogy fut-e csúszó animáció"""
        if card_key not in self._slide_animations:
            return False
        return self._slide_animations[card_key]["is_animating"]

    def reset_slide_animation(self, card_key):
        """Csúszó animáció törlése"""
        if card_key in self._slide_animations:
            del self._slide_animations[card_key]

    def reset(self):
        self._flip_progress.clear()
        self._slide_animations.clear()
        self._last_cards_count.clear()
        self._card_placed_player = None
