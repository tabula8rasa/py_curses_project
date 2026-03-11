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
    trail: deque[TailPoint] = field(default_factory=lambda: deque(maxlen=100))
    head_ch: str = "&"
    head_age: int = 0
    head_change_after: int = 20


FPS = 90
DT = 1.0 / FPS

SCALE = 3.0
G = 9.81

NUM_PARTICLES = 300

TAIL_LEN = 40

TAIL_CHANGE_BASE = 20
TAIL_CHANGE_DELTA = 5

HEAD_CHANGE_BASE = 16
HEAD_CHANGE_DELTA = 4

ARC_FRAMES = list("&80967543@XYZ")
VERTICAL_FRAMES = list("()!=*|-.")

RESTART_DELAY = 0.25


def to_screen_x(x_m: float) -> int:
    return int(round(x_m * SCALE))


def to_screen_y(y_m: float) -> int:
    return int(round(y_m * SCALE))


def random_change_delay(base: int, delta: int) -> int:
    return max(1, base + random.randint(-delta, delta))


def random_arc_char() -> str:
    return random.choice(ARC_FRAMES)


def random_vertical_char() -> str:
    return random.choice(VERTICAL_FRAMES)


def make_firework_particles(cx: float, cy: float) -> tuple[list[Particle], int]:
    particles: list[Particle] = []

    v_base = random.uniform(0, 13.5)
    vertical_start_age = random.randint(65, 120)
    vertical_fall_speed = random.uniform(6.0, 9.5)

    for i in range(NUM_PARTICLES):
        phi = 2.0 * math.pi * i / NUM_PARTICLES + random.uniform(-0.03, 0.03)
        v = v_base * random.uniform(0, 1.15)

        vx = v * math.cos(phi)
        vy = -v * math.sin(phi)

        p = Particle(
            x=cx,
            y=cy,
            vx=vx,
            vy=vy,
            trail=deque(maxlen=TAIL_LEN),
            head_ch=random_arc_char(),
            head_change_after=random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA),
        )
        particles.append(p)

    return particles, vertical_start_age, vertical_fall_speed


def run_single_firework(
    stdscr: curses.window,
    height: int,
    width: int,
    world_width_m: float,
    world_height_m: float,
) -> bool:
    cx = world_width_m * 0.5 + random.uniform(-world_width_m * 0.12, world_width_m * 0.12)
    cy = world_height_m * 0.38 + random.uniform(-world_height_m * 0.06, world_height_m * 0.05)

    particles, vertical_start_age, vertical_fall_speed = make_firework_particles(cx, cy)

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
            return False

        stdscr.erase()
        alive_count = 0

        for p in particles:
            if not p.alive:
                continue

            alive_count += 1
            vertical_mode = p.age >= vertical_start_age

            p.trail.appendleft(
                TailPoint(
                    x=p.x,
                    y=p.y,
                    ch=random_vertical_char() if vertical_mode else random_arc_char(),
                    age=0,
                    change_after=random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA),
                )
            )

            if not vertical_mode:
                p.x += p.vx * DT
                p.y += p.vy * DT
                p.vy += G * DT
            else:
                p.vx = 0.0
                p.vy = vertical_fall_speed
                p.y += p.vy * DT

            p.age += 1

            for point in p.trail:
                point.age += 1
                if point.age >= point.change_after:
                    point.ch = random_vertical_char() if vertical_mode else random_arc_char()
                    point.age = 0
                    point.change_after = random_change_delay(TAIL_CHANGE_BASE, TAIL_CHANGE_DELTA)

            p.head_age += 1
            if p.head_age >= p.head_change_after:
                p.head_ch = random_vertical_char() if vertical_mode else random_arc_char()
                p.head_age = 0
                p.head_change_after = random_change_delay(HEAD_CHANGE_BASE, HEAD_CHANGE_DELTA)

            for i, point in enumerate(p.trail):
                sx = to_screen_x(point.x)
                sy = to_screen_y(point.y)

                if 0 <= sy < height and 0 <= sx < width:
                    try:
                        draw_ch = point.ch
                        if vertical_mode and i >= int(TAIL_LEN * 0.65):
                            draw_ch = random.choice("|!.-")

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
            elif hy >= height + 2 or hy < -2 or hx >= width + 2 or hx < -2:
                p.alive = False

        stdscr.refresh()

        if alive_count == 0:
            break

    return True


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

    while True:
        height, width = stdscr.getmaxyx()
        world_width_m = width / SCALE
        world_height_m = height / SCALE

        ok = run_single_firework(stdscr, height, width, world_width_m, world_height_m)
        if not ok:
            break

        pause_start = time.perf_counter()
        while time.perf_counter() - pause_start < RESTART_DELAY:
            key = stdscr.getch()
            if key in (ord("q"), 27):
                return
            time.sleep(0.01)


if __name__ == "__main__":
    curses.wrapper(run)