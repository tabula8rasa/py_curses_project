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


@dataclass
class Particle:
    def __init__(self, phi:float, v: float, config: Config, setup: ScreenMapper, randomizer: Randomizer, stdscr: curses.window, cx: float , cy: float):

        self.x = cx
        self.y = cy
        self.vx = v * math.cos(phi)
        self.vy = -v * math.sin(phi)
        self.age: int = 0
        self.alive: bool = True
        self.show_head: bool = True
        self.head_ch: str = random.choice(config.head_frames)
        self.head_age: int = 0
        self.head_change_after: int = randomizer.random_change_delay(config.head_change_base, config.head_change_delta)
        self.death_after: int = randomizer.random_death_after()
        self.trail: deque[TailPoint] = deque(maxlen=config.tail_len)

        self.config = config
        self.setup = setup
        self.randomizer = randomizer
        self.stdscr = stdscr

    def render_particle(self):
        self.draw_tail()
        self.draw_head()

    def draw_tail(self):
        for i, point in enumerate(self.trail):
            sx = self.setup.to_screen_x(point.x)
            sy = self.setup.to_screen_y(point.y)

            if 0 <= sy < self.setup.height and 0 <= sx < self.setup.width:
                try:
                    if curses.has_colors():
                        pair = 2 if i < self.config.tail_len // 2 else 3
                        attr = curses.color_pair(pair)
                        if i < 2:
                            attr |= curses. A_BOLD
                        self.stdscr.addch(sy, sx, point.ch, attr)
                    else:
                        self.stdscr.addch(sy, sx, point.ch)
                except curses.error:
                    pass

    def draw_head(self) -> None:
        if not self.show_head:
            return
        
        hx = self.setup.to_screen_x(self.x)
        hy = self.setup.to_screen_y(self.y)

        if 0 <= hy < self.setup.height and 0 <= hx < self.setup.width:
            try:
                if curses.has_colors():
                    self.stdscr.addch(hy, hx, self.head_ch, curses.color_pair(1) | curses.A_BOLD)
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

    scale_x: float = 4.0                        # масштаб по X
    scale_y: float = 3.0                        # масштаб по Y
    
    coef_to_cx: float = 0.5
    coef_to_cy: float = 0.4

    g: float = 9.81                             # ускорение свободного падения

    v_min: float = 5.0                          # минимальная начальная скорость
    v: float = 16.1                             # базовая начальная скорость

    num_particles: int = 200                    # число частиц

    head_frames: list[str] = field(
        default_factory=lambda: list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )                                           # символы головы

    tail_frames: list[str] = field(
        default_factory=lambda: list("0123456789")
    )                                           # символы хвоста

    tail_len: int = 50                          # длина хвоста

    tail_change_base: int = 20                  # базовый интервал смены хвоста
    tail_change_delta: int = 5                  # разброс интервала хвоста

    head_change_base: int = 20                  # базовый интервал смены головы
    head_change_delta: int = 5                  # разброс интервала головы

    death_base: int = 85                        # базовое время жизни
    death_delta: int = 25                       # разброс времени жизни

    def __post_init__(self):
        if self.fps <= 0:
            raise ValueError("fps must be > 0")
        if self.scale_x <= 0 or self.scale_y <= 0:
            raise ValueError("scale_x and scale_y must be > 0")
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


class ScreenMapper:
    def __init__(self, stdscr: curses.window, config: Config):
        self.stdscr = stdscr
        self.config = config

        self.height, self.width = self.stdscr.getmaxyx()
        self.world_width_m = self.width / self.config.scale_x
        self.world_height_m = self.height / self.config.scale_y

        self.cx = self.world_width_m * self.config.coef_to_cx
        self.cy = self.world_height_m * self.config.coef_to_cy
        

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
    
    
class Timer():
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


class Firework():
    def __init__(self, config: Config, setup: ScreenMapper, randomizer: Randomizer, stdscr: curses.window):
        self.particles: list[Particle] = []
        self.cx = setup.cx + random.randint(-10, 10)
        self.cy = setup.cy + random.randint(-10, 10)
        
        for i in range(config.num_particles):
            phi = 2.0 * math.pi * i / config.num_particles
            v = random.uniform(config.v_min, config.v)
            self.particles.append(Particle(phi, v, config, setup, randomizer, stdscr, self.cx, self.cy))
    
    def render_firework(self):
        for particle in self.particles:
            if particle.alive:
                particle.render_particle()

    def update_particles(self):
        alive_count = 0

        for particle in self.particles:
            if not particle.alive:
                continue

            particle.update_state()

            if particle.alive:
                alive_count += 1
        


def run(stdscr: curses.window) -> None:

    CursesSetup.setup_screen(stdscr)

    config = Config()
    rnd = random.Random(42)
    setup = ScreenMapper(stdscr, config)
    randoomizer = Randomizer(config, rnd)

    fireworks = [Firework(config, setup, randoomizer, stdscr)]

    timer = Timer(config)
    
    while True:
        timer.wait_frame()
        timer.counter += 1

        key = stdscr.getch()
        if key in (ord("q"), 27):
            break

        stdscr.erase()
        for firework in fireworks:
            firework.update_particles()
            firework.render_firework()
            
        stdscr.refresh()

        if timer.counter == 100:
            fireworks.append(Firework(config, setup, randoomizer, stdscr))
            timer.counter = 0


if __name__ == "__main__":
    curses.wrapper(run)