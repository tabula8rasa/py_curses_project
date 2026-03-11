#!/usr/bin/env python3

import curses
import time
from collections import deque
from dataclasses import dataclass, field
import random
import math


@dataclass
class TailPoint:
    x: float
    y: float
    ch: str
    age: int = 0
    change_after: int = 20


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
        is_bold: bool
        ):

        self.x = cx
        self.y = cy
        self.vx = v * math.cos(phi)
        self.vy = -v * math.sin(phi)
        self.age: int = 0
        self.alive: bool = True
        self.show_head: bool = True
        self.head_ch: str = randomizer.rnd.choice(config.head_frames)
        self.head_age: int = 0
        self.head_change_after: int = randomizer.random_change_delay(config.head_change_base, config.head_change_delta)
        self.death_after: int = randomizer.random_death_after()
        self.trail: deque[TailPoint] = deque(maxlen=tail_len)
        self.color_scheme = randomizer.rnd.choice(color_scheme_bunch) if len(color_scheme_bunch) == 1 else color_scheme_bunch[0]
        self.tail_len = tail_len
        self.is_bold = is_bold
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

        if self.age < self.death_after:
            self._add_tail_point()
            self._update_motion()
        else:
            self._fade_particle()

        self._update_tail_symbols()
        self._update_head_symbol()

    def _add_tail_point(self) -> None:
        self.trail.appendleft(
            TailPoint(
            x=self.x,
            y=self.y,
            ch=random.choice(self.config.tail_frames),
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
        else:
            self.alive = False

    def _update_tail_symbols(self) -> None:
        for point in self.trail:
            point.age += 1
            if point.age >= point.change_after:
                point.ch = random.choice(self.config.tail_frames)
                point.age = 0
                point.change_after = self.randomizer.random_change_delay(self.config.tail_change_base, self.config.tail_change_delta)

    def _update_head_symbol(self) -> None:
        if not self.show_head:
            return
        
        self.head_age += 1
        if self.head_age >= self.head_change_after:
            self.head_ch = random.choice(self.config.head_frames)
            self.head_age = 0
            self.head_change_after = self.randomizer.random_change_delay(self.config.head_change_base, self.config.head_change_delta)


@dataclass
class Config():
    fps: int = 90                               # частота кадров в секунду
    dt: float = field(init=False)               # длительность одного кадра

    scale_x: float = 3.5                        # масштаб по X Сколько пикселей в одном метре по горизонтале
    scale_y: float = 2.0                        # масштаб по Y

    g: float = 9.81                             # ускорение свободного падения

    v_min: float = 16.0                          # минимальная начальная скорость
    v_max: float = 16.0                             # базовая начальная скорость

    num_particles_min: int = 4                    # число частиц
    num_particles_max: int = 4

    head_frames: list[str] = field(
        default_factory=lambda: list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )                                           # символы головы

    tail_frames: list[str] = field(
        default_factory=lambda: list("0123456789")
    )                                           # символы хвоста

    tail_len_min: int = 15                          # длина хвоста
    tail_len_max: int = 20

    tail_change_base: int = 20                  # базовый интервал смены хвоста
    tail_change_delta: int = 5                  # разброс интервала хвоста

    head_change_base: int = 20                  # базовый интервал смены головы
    head_change_delta: int = 5                  # разброс интервала головы

    death_base: int = 120                       # базовое время жизни
    death_delta: int = 5                        # разброс времени жизни

    is_or_not_bold = [True]              #[False]: только обычные, [True]: только жирыне, [False, True]: оба варианта

    time_delay_to_a_new_firework: int = 130

    firework_color_schemas: list[list[int]] = field(
        default_factory=lambda: [[6,9,12], [0], [0,3], [18], [12,15,18], [0,3,6,9,12,15,18], [21], [24], [27]]
    )

    def __post_init__(self):
        if self.fps <= 0:
            raise ValueError("fps must be > 0")
        if self.scale_x <= 0 or self.scale_y <= 0:
            raise ValueError("scale_x and scale_y must be > 0")
        if self.v_min > self.v_max:
            raise ValueError("v_min should not greater that v")
        self.dt = 1.0 / self.fps


class CursesSetup:
    @staticmethod
    def setup_screen(stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(0)

        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            curses.init_pair(1, curses.COLOR_YELLOW, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_MAGENTA, -1)

            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_YELLOW, -1)
            curses.init_pair(6, curses.COLOR_YELLOW, -1)

            curses.init_pair(7, curses.COLOR_CYAN, -1)
            curses.init_pair(8, curses.COLOR_CYAN, -1)
            curses.init_pair(9, curses.COLOR_CYAN, -1)

            curses.init_pair(10, curses.COLOR_BLUE, -1)
            curses.init_pair(11, curses.COLOR_BLUE, -1)
            curses.init_pair(12, curses.COLOR_BLUE, -1)

            curses.init_pair(13, curses.COLOR_MAGENTA, -1)
            curses.init_pair(14, curses.COLOR_MAGENTA, -1)
            curses.init_pair(15, curses.COLOR_MAGENTA, -1)

            curses.init_pair(16, curses.COLOR_GREEN, -1)
            curses.init_pair(17, curses.COLOR_GREEN, -1)
            curses.init_pair(18, curses.COLOR_GREEN, -1)

            curses.init_pair(19, curses.COLOR_WHITE, -1)
            curses.init_pair(20, curses.COLOR_WHITE, -1)
            curses.init_pair(21, curses.COLOR_WHITE, -1)

            # Ледяной: white -> cyan -> blue
            curses.init_pair(22, curses.COLOR_WHITE, -1)
            curses.init_pair(23, curses.COLOR_CYAN, -1)
            curses.init_pair(24, curses.COLOR_BLUE, -1)

            # Фиолетовый: white -> magenta -> blue
            curses.init_pair(25, curses.COLOR_WHITE, -1)
            curses.init_pair(26, curses.COLOR_MAGENTA, -1)
            curses.init_pair(27, curses.COLOR_BLUE, -1)

            # Изумрудный: white -> green -> cyan
            curses.init_pair(28, curses.COLOR_WHITE, -1)
            curses.init_pair(29, curses.COLOR_GREEN, -1)
            curses.init_pair(30, curses.COLOR_CYAN, -1)


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
    

class Randomizer:
    def __init__(self, config: Config, rnd: random.Random):
        self.config = config
        self.rnd = rnd

    def random_change_delay(self, base: int, delta: int) -> int:
        return max(1, base + self.rnd.randint(-delta, delta))
    
    def random_death_after(self) -> int:
        return max(
            1, 
            self.config.death_base 
            + self.rnd.randint(-self.config.death_delta, self.config.death_delta)
        )
    
    
class Timer:
    def __init__(self, config: Config):
        self.last = time.perf_counter()
        self.config = config
        self.counter = 0

    def wait_frame(self) -> None:
        now = time.perf_counter()
        elapsed = now - self.last

        if elapsed < self.config.dt:
            time.sleep(self.config.dt - elapsed)
            now = time.perf_counter()

        self.last = now


class Firework:
    def __init__(self, config: Config, setup: ScreenMapper, randomizer: Randomizer, stdscr: curses.window):

        self.cx = random.randint(int(setup.world_width_m * 0.2), int(setup.world_width_m * 0.8))
        self.cy = random.randint(int(setup.world_height_m * 0.4), int(setup.world_height_m * 0.6))

        self.color_scheme_bunch = randomizer.rnd.choice(config.firework_color_schemas)

        self.tail_len = randomizer.rnd.randint(config.tail_len_min, config.tail_len_max)
        self.num_particles = randomizer.rnd.randint(config.num_particles_min, config.num_particles_max)
        self.is_bold: bool = randomizer.rnd.choice(config.is_or_not_bold)

        self.particles: list[Particle] = self.generate_particles(config, setup, randomizer, stdscr)
        
    def generate_particles(self, config: Config, setup: ScreenMapper, randomizer: Randomizer, stdscr: curses.window):
        particles: list[Particle] = []

        for i in range(self.num_particles):
            phi = 2.0 * math.pi * i / self.num_particles
            v = random.uniform(config.v_min, config.v_max)
            particles.append(Particle(phi, v, config, setup, randomizer, stdscr, self.cx, self.cy, self.color_scheme_bunch, self.tail_len, self.is_bold))

        return particles

    def render_firework(self) -> bool:
        firework_is_alive: bool = False

        for particle in self.particles:
            if particle.alive:
                firework_is_alive = True
                particle.render_particle()

        return firework_is_alive
    
    def update_particles(self) -> None:

        for particle in self.particles:
            if not particle.alive:
                continue

            particle.update_state()
        

def run(stdscr: curses.window) -> None:

    CursesSetup.setup_screen(stdscr)

    config: Config = Config()
    setup: ScreenMapper = ScreenMapper(stdscr, config)
    randomizer: Randomizer = Randomizer(config, random.Random())

    fireworks: list[Firework]  = [Firework(config, setup, randomizer, stdscr)]

    timer: Timer = Timer(config)
    delay: float = config.time_delay_to_a_new_firework

    while True:
        timer.wait_frame()
        timer.counter += 1

        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27):
            break

        stdscr.erase()

        alive_fireworks: list[Firework] = []

        for firework in fireworks:
            firework.update_particles()
            status = firework.render_firework()
            if status:
                alive_fireworks.append(firework)

        fireworks =  alive_fireworks
            
        stdscr.refresh()

        if timer.counter == delay:
            fireworks.append(Firework(config, setup, randomizer, stdscr))
            timer.counter = 0
            delay = int(config.time_delay_to_a_new_firework - (randomizer.rnd.random()*(config.time_delay_to_a_new_firework//2)))



if __name__ == "__main__":
    curses.wrapper(run)