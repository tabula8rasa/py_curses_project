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
    x: float
    y: float
    vx: float
    vy: float
    age: int = 0
    alive: bool = True
    show_head: bool = True
    head_ch: str = "A"
    head_age: int = 0
    head_change_after: int = 20
    death_after: int = 0
    trail: deque[TailPoint] = field(default_factory=lambda: deque(maxlen=100))


FPS = 90
DT = 1.0 / FPS

# Физические параметры
SCALE_X = 4.0
SCALE_Y = 3.0
G = 9.81

# Начальные параметры броска
V_MIN = 0.0
V = 16.1

# Количество частиц в фейерверке
NUM_PARTICLES = 200

# Символы головы
HEAD_FRAMES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Символы хвоста
TAIL_FRAMES = list("0123456789")
TAIL_LEN = 50

# Базовый интервал смены символа хвоста
TAIL_CHANGE_BASE = 20
TAIL_CHANGE_DELTA = 5

# Базовый интервал смены символа головы
HEAD_CHANGE_BASE = 20
HEAD_CHANGE_DELTA = 5

# Параметры жизни частицы
DEATH_BASE = 85
DEATH_DELTA = 25


def to_screen_x(x_m: float) -> int:
    return int(round(x_m * SCALE_X))


def to_screen_y(y_m: float) -> int:
    return int(round(y_m * SCALE_Y))


def random_change_delay(base: int, delta: int) -> int:
    return max(1, base + random.randint(-delta, delta))


def random_death_after() -> int:
    return max(1, DEATH_BASE + random.randint(-DEATH_DELTA, DEATH_DELTA))


def init_curses(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_YELLOW, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)


def get_world_size(stdscr: curses.window) -> tuple[int, int, float, float]:
    height, width = stdscr.getmaxyx()
    world_width_m = width / SCALE_X
    world_height_m = height / SCALE_Y
    return height, width, world_width_m, world_height_m


def make_particle(cx: float, cy: float, phi: float, v: float) -> Particle:
    vx = v * math.cos(phi)
    vy = -v * math.sin(phi)

    return Particle(
        x=cx,
        y=cy,
        vx=vx,
        vy=vy,
        head_ch=random.choice(HEAD_FRAMES),
        head_change_after=random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA),
        death_after=random_death_after(),
        trail=deque(maxlen=TAIL_LEN),
    )


def make_particles(cx: float, cy: float) -> list[Particle]:
    particles: list[Particle] = []

    for i in range(NUM_PARTICLES):
        phi = 2.0 * math.pi * i / NUM_PARTICLES
        v = random.uniform(V_MIN, V)
        particles.append(make_particle(cx, cy, phi, v))

    return particles

...

def add_tail_point(p: Particle) -> None:
    p.trail.appendleft(
        TailPoint(
            x=p.x,
            y=p.y,
            ch=random.choice(TAIL_FRAMES),
            age=0,
            change_after=random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA),
        )
    )


def update_motion(p: Particle) -> None:
    p.x += p.vx * DT
    p.y += p.vy * DT
    p.vy += G * DT


def update_tail_symbols(p: Particle) -> None:
    for point in p.trail:
        point.age += 1
        if point.age >= point.change_after:
            point.ch = random.choice(TAIL_FRAMES)
            point.age = 0
            point.change_after = random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)


def update_head_symbol(p: Particle) -> None:
    if not p.show_head:
        return

    p.head_age += 1
    if p.head_age >= p.head_change_after:
        p.head_ch = random.choice(HEAD_FRAMES)
        p.head_age = 0
        p.head_change_after = random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA)


def fade_particle(p: Particle) -> None:
    p.show_head = False
    if p.trail:
        p.trail.pop()
    else:
        p.alive = False


def update_particle_state(p: Particle) -> None:
    if not p.alive:
        return

    p.age += 1

    if p.age < p.death_after:
        add_tail_point(p)
        update_motion(p)
    else:
        fade_particle(p)

    update_tail_symbols(p)
    update_head_symbol(p)


def draw_tail(
    stdscr: curses.window,
    p: Particle,
    height: int,
    width: int,
) -> None:
    for i, point in enumerate(p.trail):
        sx = to_screen_x(point.x)
        sy = to_screen_y(point.y)

        if 0 <= sy < height and 0 <= sx < width:
            try:
                if curses.has_colors():
                    pair = 2 if i < TAIL_LEN // 2 else 3
                    attr = curses.color_pair(pair)
                    if i < 2:
                        attr |= curses.A_BOLD
                    stdscr.addch(sy, sx, point.ch, attr)
                else:
                    stdscr.addch(sy, sx, point.ch)
            except curses.error:
                pass


def draw_head(
    stdscr: curses.window,
    p: Particle,
    height: int,
    width: int,
) -> None:
    if not p.show_head:
        return

    hx = to_screen_x(p.x)
    hy = to_screen_y(p.y)

    if 0 <= hy < height and 0 <= hx < width:
        try:
            if curses.has_colors():
                stdscr.addch(hy, hx, p.head_ch, curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.addch(hy, hx, p.head_ch)
        except curses.error:
            pass
    else:
        p.show_head = False


def render_particle(
    stdscr: curses.window,
    p: Particle,
    height: int,
    width: int,
) -> None:
    draw_tail(stdscr, p, height, width)
    draw_head(stdscr, p, height, width)


def update_particles(particles: list[Particle]) -> int:
    alive_count = 0

    for p in particles:
        if not p.alive:
            continue

        update_particle_state(p)

        if p.alive:
            alive_count += 1

    return alive_count


def render_particles(
    stdscr: curses.window,
    particles: list[Particle],
    height: int,
    width: int,
) -> None:
    for p in particles:
        if p.alive:
            render_particle(stdscr, p, height, width)


def wait_frame(last: float) -> float:
    now = time.perf_counter()
    elapsed = now - last

    if elapsed < DT:
        time.sleep(DT - elapsed)
        now = time.perf_counter()

    return now


def run(stdscr: curses.window) -> None:
    init_curses(stdscr)

    height, width, world_width_m, world_height_m = get_world_size(stdscr)

    cx = world_width_m * 0.5
    cy = world_height_m * 0.4

    particles = make_particles(cx, cy)

    last = time.perf_counter()

    while True:
        last = wait_frame(last)

        key = stdscr.getch()
        if key in (ord("q"), 27):
            break

        stdscr.erase()

        alive_count = update_particles(particles)
        render_particles(stdscr, particles, height, width)

        stdscr.refresh()

        if alive_count == 0:
            particles = make_particles(cx+random.randint(-10, 10), cy+random.randint(-10, 10))


if __name__ == "__main__":
    curses.wrapper(run)