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
    trail: deque[TailPoint] = field(default_factory=lambda: deque(maxlen=TAIL_LEN))
    head_ch: str = "&"
    head_age: int = 0
    head_change_after: int = 20


FPS = 120
DT = 1.0 / FPS

# Физические параметры
SCALE_X = 4.0
SCALE_Y = 2.0
G = 9.81

# Начальные параметры броска
V = 17.1
PHI_DEG = 45.0

# Через сколько кадров начинается строго вертикальное падение
VERTICAL_START_AGE = 150

# Скорость вертикального падения
VERTICAL_FALL_SPEED = 9.0

# Символы для обычной фазы
ARC_FRAMES = list("&80967543@XYZ")

# Символы для вертикальной фазы
VERTICAL_FRAMES = list("()!=*|-.")

TAIL_LEN = 100

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


def random_arc_char() -> str:
    return random.choice(ARC_FRAMES)


def random_vertical_char() -> str:
    return random.choice(VERTICAL_FRAMES)


def make_firework(cx: float, cy: float) -> list[Particle]:
    particles: list[Particle] = []

    num_particles = 180
    phase0 = math.radians(PHI_DEG)

    for i in range(num_particles):
        phi = phase0 + 2.0 * math.pi * i / num_particles

        # Скорость около V, но с разбросом
        speed = V * random.uniform(0.65, 1.0)

        vx = speed * math.cos(phi)
        vy = -speed * math.sin(phi)

        particles.append(
            Particle(
                x=cx,
                y=cy,
                vx=vx,
                vy=vy,
                head_ch=random_arc_char(),
                head_change_after=random_change_delay(
                    HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA
                ),
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

    world_width_m = width / SCALE_X
    world_height_m = height / SCALE_Y

    particles = make_firework(
        cx=world_width_m * 0.5,
        cy=world_height_m * 0.5,
    )

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

            vertical_mode = p.age >= VERTICAL_START_AGE

            # Добавляем новую точку хвоста
            p.trail.appendleft(
                TailPoint(
                    x=p.x,
                    y=p.y,
                    ch=random_vertical_char() if vertical_mode else random_arc_char(),
                    age=0,
                    change_after=random_change_delay(
                        TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA
                    ),
                )
            )

            # Обновление физики частицы
            if not vertical_mode:
                p.x += p.vx * DT
                p.y += p.vy * DT
                p.vy += G * DT
            else:
                p.vx = 0.0
                p.vy = VERTICAL_FALL_SPEED
                p.y += p.vy * DT

            p.age += 1

            # Обновление символов хвоста
            for point in p.trail:
                point.age += 1
                if point.age >= point.change_after:
                    point.ch = (
                        random_vertical_char() if vertical_mode else random_arc_char()
                    )
                    point.age = 0
                    point.change_after = random_change_delay(
                        TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA
                    )

            # Обновление символа головы
            p.head_age += 1
            if p.head_age >= p.head_change_after:
                p.head_ch = (
                    random_vertical_char() if vertical_mode else random_arc_char()
                )
                p.head_age = 0
                p.head_change_after = random_change_delay(
                    HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA
                )

            # Хвост
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

            # Голова
            hx = to_screen_x(p.x)
            hy = to_screen_y(p.y)

            if 0 <= hy < height and 0 <= hx < width:
                try:
                    if curses.has_colors():
                        stdscr.addch(
                            hy, hx, p.head_ch, curses.color_pair(1) | curses.A_BOLD
                        )
                    else:
                        stdscr.addch(hy, hx, p.head_ch)
                except curses.error:
                    pass
            else:
                p.alive = False
                continue

            alive_count += 1

        stdscr.refresh()

        if alive_count == 0:
            break


if __name__ == "__main__":
    curses.wrapper(run)