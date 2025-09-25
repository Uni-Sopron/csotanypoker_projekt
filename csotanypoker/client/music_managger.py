import pygame


class MusicManager:
    def __init__(
        self, music_file: str = "csotanypoker/client/music/background_music.mp3"
    ) -> None:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        self.music_file = music_file
        self.music_volume = 0.02   
        self._load_music()
    def _load_music(self) -> None:
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.set_volume(self.music_volume)


    def start_background_music(self) -> None:
        pygame.mixer.music.play(-1)
             

    def set_volume(self, volume: float) -> None:
        self.music_volume = volume
        pygame.mixer.music.set_volume(self.music_volume)
