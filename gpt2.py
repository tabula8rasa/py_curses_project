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
    head_ch: str = "A"
    head_age: int = 0
    head_change_after: int = 20
    trail: deque[TailPoint] = field(default_factory=lambda: deque(maxlen=100))


FPS = 90
DT = 1.0 / FPS

# Физические параметры
SCALE = 3.0
G = 9.81

SCALE_X = 4.0
SCALE_Y = 2.0

# Частицы
NUM_PARTICLES = 200
V_MAX = 10.0

# Символы головы
HEAD_FRAMES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Символы хвоста
TAIL_FRAMES = list("abcdefghijklmnopqrstuvwxyz")
TAIL_LEN = 15

# Базовый интервал смены символа хвоста
TAIL_CHANGE_BASE = 20
TAIL_CHANGE_DELTA = 5

# Базовый интервал смены символа головы
HEAD_CHANGE_BASE = 20
HEAD_CHANGE_DELTA = 5

def to_screen_x(x_m: float) -> int:
    return int(round(x_m * SCALE_X))

def to_screen_y(y_m: float) -> int:
    return int(round(y_m * SCALE_Y))


def random_change_delay(base: int, delta: int) -> int:
    return max(1, base + random.randint(-delta, delta))


def make_particles(cx: float, cy: float) -> list[Particle]:
    particles: list[Particle] = []

    for i in range(NUM_PARTICLES):
        phi = 2.0 * math.pi * i / NUM_PARTICLES
        v = random.uniform(0.0, V_MAX)

        vx = v * math.cos(phi)
        vy = -v * math.sin(phi)  # минус, потому что экранная ось y направлена вниз

        particles.append(
            Particle(
                x=cx,
                y=cy,
                vx=vx,
                vy=vy,
                head_ch=random.choice(HEAD_FRAMES),
                head_change_after=random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA),
                trail=deque(maxlen=TAIL_LEN),
            )
        )

    return particles


def run(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_YELLOW, -1)   # голова
        curses.init_pair(2, curses.COLOR_RED, -1)      # ближний хвост
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)  # дальний хвост

    height, width = stdscr.getmaxyx()
    world_width_m = width / SCALE
    world_height_m = height / SCALE

    cx = world_width_m * 0.5
    cy = world_height_m * 0.5

    particles = make_particles(cx, cy)

    last = time.perf_counter()

    while True:
        now = time.perf_counter()
        elapsed = now - last

        if elapsed < DT:
            time.sleep(DT - elapsed)
            now = time.perf_counter()
            elapsed = now - last

        last = now

        key = stdscr.getch()
        if key in (ord("q"), 27):
            break

        stdscr.erase()

        alive_count = 0

        for p in particles:
            if not p.alive:
                continue

            alive_count += 1

            # Добавляем новую точку хвоста
            p.trail.appendleft(
                TailPoint(
                    x=p.x,
                    y=p.y,
                    ch=random.choice(TAIL_FRAMES),
                    age=0,
                    change_after=random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)
                )
            )

            # Обновление физики
            p.x += p.vx * DT
            p.y += p.vy * DT
            p.vy += G * DT
            p.age += 1

            # Обновление символов хвоста
            for point in p.trail:
                point.age += 1
                if point.age >= point.change_after:
                    point.ch = random.choice(TAIL_FRAMES)
                    point.age = 0
                    point.change_after = random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)

            # Обновление символа головы
            p.head_age += 1
            if p.head_age >= p.head_change_after:
                p.head_ch = random.choice(HEAD_FRAMES)
                p.head_age = 0
                p.head_change_after = random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA)

            # Рисуем хвост
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

            # Рисуем голову
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
                p.alive = False

        stdscr.refresh()

        if alive_count == 0:
            break


if __name__ == "__main__":
    curses.wrapper(run)