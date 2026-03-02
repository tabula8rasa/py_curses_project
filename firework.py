import curses
import math
import random
import time
from dataclasses import dataclass


FPS = 60
GRAVITY = 18.0
SPAWN_CHANCE = 0.08


@dataclass
class Rocket:
    x: float
    y: float
    vy: float
    color: int


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    char: str
    color: int


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_BLUE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)


def spawn_rocket(width: int, height: int) -> Rocket:
    return Rocket(
        x=random.uniform(width * 0.2, width * 0.8),
        y=height - 2,
        vy=random.uniform(-28.0, -22.0),
        color=random.randint(1, 7),
    )


def explode(rocket: Rocket) -> list[Particle]:
    particles = []
    count = random.randint(35, 70)

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4.0, 16.0)

        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        particles.append(
            Particle(
                x=rocket.x,
                y=rocket.y,
                vx=vx,
                vy=vy,
                life=random.uniform(0.8, 1.6),
                max_life=1.6,
                char=random.choice(["*", ".", "+", "·"]),
                color=random.randint(1, 7),
            )
        )

    return particles


def draw_safe(stdscr, y: int, x: int, ch: str, attr: int = 0):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        try:
            stdscr.addstr(y, x, ch, attr)
        except curses.error:
            pass


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    init_colors()

    rockets: list[Rocket] = []
    particles: list[Particle] = []

    last_time = time.perf_counter()

    while True:
        now = time.perf_counter()
        dt = now - last_time
        last_time = now
        dt = min(dt, 0.05)

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q")):
            break

        if random.random() < SPAWN_CHANCE:
            rockets.append(spawn_rocket(w, h))

        # Обновление ракет
        new_rockets = []
        for r in rockets:
            r.y += r.vy * dt
            r.vy += GRAVITY * dt * 0.35

            # момент взрыва
            if r.vy >= -2.0:
                particles.extend(explode(r))
            else:
                new_rockets.append(r)

        rockets = new_rockets

        # Обновление частиц
        new_particles = []
        for p in particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += GRAVITY * dt
            p.life -= dt

            if p.life > 0:
                new_particles.append(p)

        particles = new_particles

        # Рисуем ракеты
        for r in rockets:
            draw_safe(
                stdscr,
                int(r.y),
                int(r.x),
                "|",
                curses.color_pair(r.color) | curses.A_BOLD,
            )

        # Рисуем частицы
        for p in particles:
            fade = p.life / p.max_life

            attr = curses.color_pair(p.color)
            if fade > 0.6:
                attr |= curses.A_BOLD

            char = p.char
            if fade < 0.25:
                char = "."
            elif fade < 0.45:
                char = "·"

            draw_safe(stdscr, int(p.y), int(p.x), char, attr)

        hint = "Q - quit"
        draw_safe(stdscr, h - 1, 1, hint, curses.color_pair(7))

        stdscr.refresh()
        time.sleep(1 / FPS)


def main():
    curses.wrapper(run)


if __name__ == "__main__":
    main()