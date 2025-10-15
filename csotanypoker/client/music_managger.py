import pygame
from typing import Dict


class MusicManager:
    def __init__(
        self, music_file: str = "csotanypoker/client/music/samurai-heart-290878.mp3"
    ) -> None:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        self.music_file = music_file
        self.music_volume = 0.02
        self.sound_effects_enabled = True
        self.sound_effects_volume = 0.1

        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self._load_sounds()
        self._load_background_music()

    def _load_background_music(self) -> None:
        pygame.mixer.music.load(self.music_file)
        pygame.mixer.music.set_volume(self.music_volume)

    def _load_sounds(self) -> None:
        sound_files = {
            "start_game": "csotanypoker/client/music/game-start-317318.mp3",
            "win_game": "csotanypoker/client/music/brass-144755.mp3",
            "lose_game": "csotanypoker/client/music/fail-144746.mp3",
            "button_click": "csotanypoker/client/music/zapsplat_multimedia_button_click_bright_002_92099.mp3",
            "invalid_click": "csotanypoker/client/music/zapsplat_multimedia_error_incorrect_buzz_73714.mp3",
            "rat_weapon": "csotanypoker/client/music/sword-blade-slicing-flesh-352708.mp3",
            "spider_weapon": "csotanypoker/client/music/steel-chain-dragged-shower-reverb-106252.mp3",
            "scorpion_weapon": "csotanypoker/client/music/ground-impact-352053.mp3",
            "fly_weapon": "csotanypoker/client/music/zapsplat_warfare_throwing_star_throw_spin_hit_person_squelch_blood_20926.mp3",
            "cockroach_weapon": "csotanypoker/client/music/sword-slice-393847.mp3",
            "toad_weapon": "csotanypoker/client/music/giant-fall-impact-352446.mp3",
            "bat_weapon": "csotanypoker/client/music/foley_walkers_suriken+3.mp3",
            "bedbug_weapon": "csotanypoker/client/music/swoosh-142322.mp3",
            "leave": "csotanypoker/client/music/interface-124464.mp3",
            "join": "csotanypoker/client/music/interface-124464.mp3",
        }

        for sound_name, file_path in sound_files.items():
            try:
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(self.sound_effects_volume)
                self.sounds[sound_name] = sound
            except pygame.error as e:
                print(f"Nem sikerült betölteni a hangfájlt {file_path}: {e}")

    def connect_sound(self) -> None:
        self._play_sound("join")

    def _play_sound(self, sound_name: str) -> None:
        if self.sound_effects_enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def invalid_click_sound(self) -> None:
        self._play_sound("invalid_click")

    def start_game_sound(self) -> None:
        self._play_sound("start_game")

    def win_sound(self) -> None:
        self._play_sound("win_game")

    def lose_sound(self) -> None:
        self._play_sound("lose_game")

    def button_click_sound(self) -> None:
        self._play_sound("button_click")

    def start_background_music(self) -> None:
        pygame.mixer.music.play(-1)

    def stop_background_music(self) -> None:
        pygame.mixer.music.stop()

    def weapon_sound(self, animal) -> None:
        self._play_sound(f"{animal}_weapon")

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sound_effects_volume(self, volume: float) -> None:
        self.sound_effects_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_effects_volume)

    def enable_sound_effects(self) -> None:
        self.sound_effects_enabled = True

    def disable_sound_effects(self) -> None:
        self.sound_effects_enabled = False

    def toggle_sound_effects(self) -> bool:
        self.sound_effects_enabled = not self.sound_effects_enabled
        return self.sound_effects_enabled
