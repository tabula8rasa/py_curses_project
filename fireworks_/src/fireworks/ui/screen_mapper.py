import curses
from fireworks.config import Config

class ScreenMapper:
    def __init__(self, stdscr: curses.window, config: Config):
        self.stdscr = stdscr
        self.config = config

        self.height, self.width = self.stdscr.getmaxyx()
        self.world_width_m = self.width / self.config.scale_x
        self.world_height_m = self.height / self.config.scale_y

    def to_screen_x(self, x: float) -> int:
        return int(round(x * self.config.scale_x))

    def to_screen_y(self, y: float) -> int:
        return int(round(y * self.config.scale_y))
