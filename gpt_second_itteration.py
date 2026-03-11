import curses
import time
from collections import deque
from dataclasses import dataclass
import random
import math


@dataclass
class Particle:
    x: float      # метры
    y: float      # метры
    vx: float     # м/с
    vy: float     # м/с
    age: int = 0


@dataclass
class TailPoint:
    x: float
    y: float
    ch: str
    age: int = 0
    change_after: int = 20


FPS = 90
DT = 1.0 / FPS

# Физические параметры
SCALE_X = 4.0
SCALE_Y = 3.0
G = 9.81

# Начальные параметры броска
V = 12.1          # модуль скорости, м/с
PHI_DEG = 45.0    # угол к горизонту, градусов

# Символы головы
HEAD_FRAMES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Символы хвоста
TAIL_FRAMES = list("abcdefghijklmnopqrstuvwxyz")
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

    phi = math.radians(PHI_DEG)
    vx0 = V * math.cos(phi)
    vy0 = -V * math.sin(phi)

    p = Particle(
        x=world_width_m * 0.5,
        y=world_height_m * 0.70,
        vx=vx0,
        vy=vy0
    )

    trail: deque[TailPoint] = deque(maxlen=TAIL_LEN)

    last = time.perf_counter()

    head_ch = random.choice(HEAD_FRAMES)
    head_age = 0
    head_change_after = random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA)

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

        # Добавляем новую точку хвоста
        trail.appendleft(
            TailPoint(
                x=p.x,
                y=p.y,
                ch=random.choice(TAIL_FRAMES),
                age=0,
                change_after=random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)
            )
        )

        # Обновление физики частицы
        p.x += p.vx * DT
        p.y += p.vy * DT
        p.vy += G * DT
        p.age += 1

        # Обновление символов хвоста независимо друг от друга
        for point in trail:
            point.age += 1
            if point.age >= point.change_after:
                point.ch = random.choice(TAIL_FRAMES)
                point.age = 0
                point.change_after = random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)

        # Обновление символа головы
        head_age += 1
        if head_age >= head_change_after:
            head_ch = random.choice(HEAD_FRAMES)
            head_age = 0
            head_change_after = random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA)

        # Рендер
        stdscr.erase()

        # Хвост
        for i, point in enumerate(trail):
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
                    stdscr.addch(hy, hx, head_ch, curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addch(hy, hx, head_ch)
            except curses.error:
                pass

        stdscr.refresh()

        # Выход, если частица улетела далеко
        if hx >= width + 2 or hy >= height + 2 or hy < -2:
            break


if __name__ == "__main__":
    curses.wrapper(run)
