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
HEAD_FRAMES = list("&80967543@XYZ")

# Символы хвоста
TAIL_FRAMES = list("abcdefghijklmnopqrstuvwxyz")
TAIL_FRAMES = list("&80967543@XYZ")
TAIL_LEN = 30

# Базовый интервал смены символа хвоста
TAIL_CHANGE_BASE = 20
TAIL_CHANGE_DELTA = 5

# Базовый интервал смены символа головы
HEAD_CHANGE_BASE = 20
HEAD_CHANGE_DELTA = 5

# Как часто создавать новый фейерверк
SPAWN_INTERVAL_FRAMES = 18

# Сколько максимум фейерверков держать одновременно
MAX_FIREWORKS = 9


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
        vy = -v * math.sin(phi)

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
        curses.init_pair(1, curses.COLOR_YELLOW, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)

    height, width = stdscr.getmaxyx()
    world_width_m = width / SCALE_X
    world_height_m = height / SCALE_Y

    fireworks: list[list[Particle]] = []
    frame_counter = 0

    while True:
        now = time.perf_counter()

        key = stdscr.getch()
        if key in (ord("q"), 27):
            break

        # Периодически создаем новый фейерверк, не дожидаясь исчезновения предыдущих
        if frame_counter % SPAWN_INTERVAL_FRAMES == 0:
            cx = random.uniform(world_width_m * 0.20, world_width_m * 0.80)
            cy = random.uniform(world_height_m * 0.20, world_height_m * 0.65)
            fireworks.append(make_particles(cx, cy))

            if len(fireworks) > MAX_FIREWORKS:
                fireworks.pop(0)

        stdscr.erase()

        alive_fireworks: list[list[Particle]] = []

        for particles in fireworks:
            alive_count = 0

            for p in particles:
                if not p.alive:
                    continue

                alive_count += 1

                p.trail.appendleft(
                    TailPoint(
                        x=p.x,
                        y=p.y,
                        ch=random.choice(TAIL_FRAMES),
                        age=0,
                        change_after=random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)
                    )
                )

                p.x += p.vx * DT
                p.y += p.vy * DT
                p.vy += G * DT
                p.age += 1

                for point in p.trail:
                    point.age += 1
                    if point.age >= point.change_after:
                        point.ch = random.choice(TAIL_FRAMES)
                        point.age = 0
                        point.change_after = random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)

                p.head_age += 1
                if p.head_age >= p.head_change_after:
                    p.head_ch = random.choice(HEAD_FRAMES)
                    p.head_age = 0
                    p.head_change_after = random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA)

                for i, point in enumerate(p.trail):
                    sx = to_screen_x(point.x)
                    sy = to_screen_y(point.y)

                    if 0 <= sy < height and 0 <= sx < width:
                        try:
                            draw_ch = point.ch
                            if i >= int(TAIL_LEN * 0.7):
                                draw_ch = "."

                            if curses.has_colors():
                                pair = 2 if i < TAIL_LEN // 2 else 3
                                attr = curses.color_pair(pair)
                                if i < 2:
                                    attr |= curses.A_BOLD
                                stdscr.addch(sy, sx, draw_ch, attr)
                            else:
                                stdscr.addch(sy, sx, draw_ch)
                        except curses.error:
                            pass

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

            if alive_count > 0:
                alive_fireworks.append(particles)

        fireworks = alive_fireworks

        stdscr.refresh()
        frame_counter += 1

        elapsed = time.perf_counter() - now
        if elapsed < DT:
            time.sleep(DT - elapsed)


if __name__ == "__main__":
    curses.wrapper(run)