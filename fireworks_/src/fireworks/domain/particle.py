from __future__ import annotations

import curses
from collections import deque
import math

from fireworks.config import Config
from fireworks.domain.tail_point import TailPoint
from fireworks.services.randomizer import Randomizer
from fireworks.ui.screen_mapper import ScreenMapper

class Particle:
    def __init__(self,
        phi:float, 
        v: float, 
        config: Config, 
        setup: ScreenMapper, 
        randomizer: Randomizer, 
        stdscr: curses.window, 
        cx: float, 
        cy: float,
        color_scheme_bunch: list[int],
        tail_len: int,
        is_bold: bool,
        has_confetti: bool
        ):

        self.x = cx
        self.y = cy
        self.vx = v * math.cos(phi)
        self.vy = -v * math.sin(phi)
        self.age: int = 0
        self.alive: bool = True
        self.fading: bool = False
        self.show_head: bool = True
        self.head_ch: str = randomizer.rnd.choice(config.head_frames)
        self.head_age: int = 0
        self.head_change_after: int = randomizer.random_change_delay(config.head_change_base, config.head_change_delta)
        self.death_after: int = randomizer.random_death_after()
        self.trail: deque[TailPoint] = deque(maxlen=tail_len)
        self.color_scheme = randomizer.rnd.choice(color_scheme_bunch) if len(color_scheme_bunch) == 1 else color_scheme_bunch[0]
        self.tail_len = tail_len
        self.is_bold = is_bold
        self.has_confetti: bool = has_confetti
        self.confetti_mode: bool = False
        self.confetti_age: int = 0
        self.confetti_lifetime: int = randomizer.rnd.randint(config.confetti_lifetime_min, config.confetti_lifetime_max)
        self.confetti_vy: float = config.confetti_init_vy
        self.confetti_ch: str = randomizer.rnd.choice(config.confetti_frames)

        self.config = config
        self.setup = setup
        self.randomizer = randomizer
        self.stdscr = stdscr

    def render_particle(self) -> None:
        self._draw_tail()
        self._draw_head()

    def _draw_tail(self) -> None:
        for i, point in enumerate(self.trail):
            sx = self.setup.to_screen_x(point.x)
            sy = self.setup.to_screen_y(point.y)

            if 0 <= sy < self.setup.height and 0 <= sx < self.setup.width:
                try:
                    if curses.has_colors():
                        if self.age < self.death_after:
                            pair = self.color_scheme + 2 if i < self.tail_len // 2 else self.color_scheme + 3
                        else:
                            pair = self.color_scheme + 3
                        attr = curses.color_pair(pair)
                        if self.is_bold:
                            attr |= curses.A_BOLD
                        self.stdscr.addch(sy, sx, point.ch, attr)
                    else:
                        self.stdscr.addch(sy, sx, point.ch)
                except curses.error:
                    pass

    def _draw_head(self) -> None:

        if self.confetti_mode and self.has_confetti:
            hx = self.setup.to_screen_x(self.x)
            hy = self.setup.to_screen_y(self.y)

            if 0 <= hy < self.setup.height and 0 <= hx < self.setup.width:
                try:
                    attr = curses.color_pair(self.color_scheme + 3)
                    self.stdscr.addch(hy, hx, self.confetti_ch, attr)
                except curses.error:
                    pass
            else:
                self.alive = False
            return
        
        if not self.show_head:
            return
        
        hx = self.setup.to_screen_x(self.x)
        hy = self.setup.to_screen_y(self.y)

        if 0 <= hy < self.setup.height and 0 <= hx < self.setup.width:
            try:
                if curses.has_colors():
                    attr = curses.color_pair(self.color_scheme + 1)
                    if self.is_bold:
                        attr |= curses.A_BOLD
                    self.stdscr.addch(hy, hx, self.head_ch, attr)
                else:
                    self.stdscr.addch(hy, hx, self.head_ch)
            except curses.error:
                pass
        else:
            self.show_head = False

    def update_state(self) -> None:
        if not self.alive:
            return

        self.age += 1

        if self.fading:
            self._fade_particle()
            if not self.trail:
                self.alive = False
            return

        if not self.confetti_mode:
            if self.age < self.death_after:
                self._add_tail_point()
                self._update_motion()
                self._update_tail_symbols()
                self._update_head_symbol()
            elif self.has_confetti:
                self.confetti_mode = True
                self.confetti_age = 0
            else:
                self.fading = True
                self.show_head = False
        else:
            self._add_tail_point()
            self._update_confetti_motion()
            self._update_confetti_symbols()
            self.confetti_age += 1

            if self.confetti_age >= self.confetti_lifetime:
                self.alive = False

    def _update_confetti_motion(self) -> None:
        self.vx = 0.0
        self.vy = self.confetti_vy
        self.y += self.vy * self.config.dt

    def _update_confetti_symbols(self) -> None:
        self.head_age += 1
        if self.head_age >= self.head_change_after:
            self.confetti_ch = self.randomizer.rnd.choice(self.config.confetti_frames)
            self.head_age = 0
            self.head_change_after = self.randomizer.random_change_delay(
                self.config.head_change_base,
                self.config.head_change_delta,
            )

        for point in self.trail:
            point.age += 1
            if point.age >= point.change_after:
                point.ch = self.randomizer.rnd.choice(self.config.confetti_frames)
                point.age = 0
                point.change_after = self.randomizer.random_change_delay(
                    self.config.tail_change_base,
                    self.config.tail_change_delta,
            )

    def _add_tail_point(self) -> None:
        self.trail.appendleft(
            TailPoint(
            x=self.x,
            y=self.y,
            ch=self.randomizer.rnd.choice(self.config.confetti_frames if self.confetti_mode else self.config.tail_frames),
            age=0,
            change_after=self.randomizer.random_change_delay(self.config.tail_change_base, self.config.tail_change_delta),
        )
    )

    def _update_motion(self) -> None:
        self.x += self.vx * self.config.dt
        self.y += self.vy * self.config.dt
        self.vy += self.config.g * self.config.dt

    def _fade_particle(self) -> None:
        self.show_head = False

        if self.trail:
            self.trail.pop()

    def _update_tail_symbols(self) -> None:
        for point in self.trail:
            point.age += 1
            if point.age >= point.change_after:
                point.ch = self.randomizer.rnd.choice(self.config.tail_frames)
                point.age = 0
                point.change_after = self.randomizer.random_change_delay(self.config.tail_change_base, self.config.tail_change_delta)

    def _update_head_symbol(self) -> None:
        if not self.show_head:
            return
        
        self.head_age += 1
        if self.head_age >= self.head_change_after:
            self.head_ch = self.randomizer.rnd.choice(self.config.head_frames)
            self.head_age = 0
            self.head_change_after = self.randomizer.random_change_delay(self.config.head_change_base, self.config.head_change_delta)
