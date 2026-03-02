#!/usr/bin/env python3

import curses, random, time
from collections import deque
from dataclasses import dataclass
from typing import Final, Protocol, cast

SPEED_MUL: Final[float] = 2.0
FPS: Final[int] = 120
SYMBOLS: Final[list[str]] = list(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "!@#$%^&*()-_=+[]{};:'\",.<>?/\\|`~"
)

class WindowLike(Protocol):
    def getmaxyx(self) -> tuple[int, int]: ...
    def getch(self) -> int: ...
    def erase(self) -> None: ...
    def addch(self, y: int, x: int, ch: str, attr: int = 0) -> None: ...
    def addstr(self, y: int, x: int, s: str) -> None: ...
    def nodelay(self, flag: bool) -> None: ...
    def keypad(self, flag: bool) -> None: ...
    def bkgd(self, ch: str, attr: int) -> None: ...
    def refresh(self) -> None: ...

@dataclass
class Drop:
    x: int
    y: float
    speed: float
    length: int
    trail: deque[tuple[int, str, int]]

@dataclass
class State:
    height: int
    width: int
    drops: list[Drop]
    speed_mul: float
    has_colors: bool
    tail_pair: tuple[int, str]
    digit_colors: dict[int, tuple[int, str]]
    bold_front: bool
    FPS: int
    frame_ms: int
    last: float

def init_drops(width: int, height: int) -> list[Drop]:
    drops: list[Drop] = []
    for x in range(width):
        drops.append(new_drop(x, height))
    return drops

def new_drop(x: int, height: int) -> Drop:
    y0 = random.uniform(-height,0)
    speed = random.uniform(10.0, 15.0)
    length = random.randint(max(4, height // 4), max(6, height * 2 // 3))
    return Drop(x=x, y=y0, speed=speed, length=length, trail=deque(maxlen=length))

def setup(stdscr: WindowLike, SPEED_MUL: float, FPS: int) -> State:

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    has_colors = curses.has_colors()
    if has_colors:

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_BLACK)  
        curses.init_pair(2, curses.COLOR_GREEN,   curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED,     curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE,    curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN,    curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_WHITE,   curses.COLOR_BLACK)
        stdscr.bkgd(' ', curses.color_pair(1))

        digit_colors_keys = {
                ord('!'): (2, 'Green  '),
                ord('@'): (3, 'Red    '),
                ord('#'): (4, 'Blue   '),
                ord('$'): (5, 'Yellow '),
                ord('%'): (6, 'Cyan   '),
                ord('^'): (7, 'Magenta'),
                ord('&'): (8, 'White  '),
                ord('*'): (9, 'Rainbow')
            }

        tail_pair_default = digit_colors_keys[ord('!')]
    else:
        digit_colors_keys = {}
        tail_pair_default = (2, 'Green  ')

    height, width = stdscr.getmaxyx()
    drops = init_drops(width, height)

    frame_ms = int(1000 / FPS)
    last = time.perf_counter()


    return State(
        height=height,
        width=width,
        drops=drops,
        speed_mul=SPEED_MUL,
        has_colors=has_colors,
        tail_pair=tail_pair_default,
        digit_colors=digit_colors_keys,
        bold_front=False,
        FPS=FPS,
        frame_ms=frame_ms,
        last=last,
    )

def handle_input(stdscr: WindowLike, s: State) -> bool:
    ch = stdscr.getch()
    
    if ch == -1:
        return True 

    if ch in (ord('q'), ord('Q')):
        return False

    elif 48 <= ch <= 57:
        digit = ch - 48
        s.speed_mul = digit if digit != 0 else 10

    elif ch in (ord('r'), ord('R')):
        stdscr.erase()
        s.height, s.width = stdscr.getmaxyx()
        s.drops = init_drops(s.width, s.height)
    
    elif ch in (ord('b'), ord('B')):
        s.bold_front = False if s.bold_front else True

    elif ch in s.digit_colors:
        s.tail_pair = s.digit_colors[ch]
        if s.tail_pair[0] == 9:
            rainbow_recolor_all(s)

    return True

def handle_resize(stdscr: WindowLike, s: State) -> None:
    h2, w2 = stdscr.getmaxyx()
    if (h2, w2) != (s.height, s.width):
        s.height, s.width = h2, w2
        stdscr.erase()
        s.drops = init_drops(s.width, s.height)

def pick_color_id(s: State) -> int:
    color_id = s.tail_pair[0]
    if color_id == 9:
        return random.choice([2, 3, 4, 5, 6, 7, 8])
    return color_id

def rainbow_recolor_all(s: State) -> None:
    palette = list(range(2, len(s.digit_colors)+1))
    for d in s.drops:
        d.trail = deque(
            ((row, sym, random.choice(palette)) for (row, sym, _) in d.trail),
            maxlen=d.trail.maxlen
        )

def update_and_draw(stdscr: WindowLike, s: State, dt: float) -> None:
    for d in s.drops:
        old_head_row = int(d.y)
        d.y += d.speed * s.speed_mul * dt
        new_head_row = int(d.y)

        if new_head_row > old_head_row:
            for row in range(old_head_row + 1, new_head_row + 1):
                sym = random.choice(SYMBOLS)
                color_id = pick_color_id(s)

                if len(d.trail) == d.trail.maxlen:
                    tail_row, _, _ = d.trail.pop()
                    if 0 <= tail_row < s.height:
                        try:
                            stdscr.addch(tail_row, d.x, ' ')
                        except curses.error:
                            pass

                d.trail.appendleft((row, sym, color_id))

        if new_head_row - d.length > s.height:
            for row, _, _ in d.trail:
                if 0 <= row < s.height:
                    try:
                        stdscr.addch(row, d.x, ' ')
                    except curses.error:
                        pass
            nd = new_drop(d.x, s.height)
            d.y, d.speed, d.length, d.trail = nd.y, nd.speed, nd.length, nd.trail
            continue

        for idx, (row, sym, color_id) in enumerate(d.trail):
            if not (0 <= row < s.height):
                continue

            if s.has_colors:
                head_attr = curses.color_pair(1) | curses.A_BOLD
                tail_attr = curses.color_pair(color_id if s.tail_pair[0]==9 else s.tail_pair[0]) | (curses.A_BOLD if s.bold_front else 0)
                attr = head_attr if idx == 0 else tail_attr

            else:
                attr = curses.A_BOLD if (idx == 0 or s.bold_front) else 0

            try:
                stdscr.addch(row, d.x, sym, attr)
            except curses.error:
                pass

def draw_hint(stdscr: WindowLike, s: State) -> None:
    hint = f" q:quit  r:reset  0-9:speed x{s.speed_mul:.1f} !-&:color {s.tail_pair[1]} b:bold_front {s.bold_front}"
    if s.height > 1:
        try:
            stdscr.addstr(s.height - 1, 0, hint[:max(0, s.width - 1)])
        except curses.error:
            pass

def tick_time(s: State) -> float:
    now = time.perf_counter()
    dt = now - s.last
    s.last = now
    return min(dt, 0.1)

def run(stdscr: curses.window) -> None:
    screen = cast(WindowLike, stdscr)

    s = setup(screen, SPEED_MUL, FPS)

    while True:
        dt = tick_time(s)

        if not handle_input(screen, s):
            break

        handle_resize(screen, s)
        update_and_draw(screen, s, dt)
        draw_hint(screen, s)

        screen.refresh()
        curses.napms(s.frame_ms)

def main():
    curses.wrapper(run)

if __name__ == "__main__":
    main()
