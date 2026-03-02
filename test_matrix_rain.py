#!/usr/bin/env python3
# Запуск: pytest -q

from __future__ import annotations

from collections import deque
from typing import Any, Protocol, cast

from pytest import MonkeyPatch 

import pmatrix as m


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


class FakeCursesError(Exception):
    pass


class FakeWindow:
    """Минимальная заглушка curses.window, которая записывает вызовы."""

    def __init__(self, h: int = 24, w: int = 80, keys: list[int] | None = None) -> None:
        self._h = h
        self._w = w
        self._keys = list(keys) if keys is not None else []
        self.calls: list[tuple[Any, ...]] = []

    def getmaxyx(self) -> tuple[int, int]:
        return self._h, self._w

    def setmaxyx(self, h: int, w: int) -> None:
        self._h = h
        self._w = w

    def getch(self) -> int:
        if not self._keys:
            return -1
        return self._keys.pop(0)

    def erase(self) -> None:
        self.calls.append(("erase",))

    def addch(self, y: int, x: int, ch: str, attr: int = 0) -> None:
        self.calls.append(("addch", y, x, ch, attr))

    def addstr(self, y: int, x: int, s: str) -> None:
        self.calls.append(("addstr", y, x, s))

    def nodelay(self, flag: bool) -> None:
        self.calls.append(("nodelay", flag))

    def keypad(self, flag: bool) -> None:
        self.calls.append(("keypad", flag))

    def bkgd(self, ch: str, attr: int) -> None:
        self.calls.append(("bkgd", ch, attr))

    def refresh(self) -> None:
        self.calls.append(("refresh",))


def make_state(
    *,
    height: int = 10,
    width: int = 5,
    drops: list[m.Drop] | None = None,
    speed_mul: float = 1.0,
    has_colors: bool = False,
    tail_pair: tuple[int, str] = (2, "Green"),
    digit_colors: dict[int, tuple[int, str]] | None = None,
    bold_front: bool = False,
    FPS: int = 120,
    frame_ms: int = 8,
    last: float = 0.0,
) -> m.State:
    if drops is None:
        drops = []
    if digit_colors is None:
        digit_colors = {}
    return m.State(
        height=height,
        width=width,
        drops=drops,
        speed_mul=speed_mul,
        has_colors=has_colors,
        tail_pair=tail_pair,
        digit_colors=digit_colors,
        bold_front=bold_front,
        FPS=FPS,
        frame_ms=frame_ms,
        last=last,
    )


def test_new_drop_ranges(monkeypatch: MonkeyPatch) -> None:
    def fake_uniform(a: float, b: float) -> float:
        return (a + b) / 2

    def fake_randint(a: int, b: int) -> int:
        return a

    monkeypatch.setattr(m.random, "uniform", fake_uniform)
    monkeypatch.setattr(m.random, "randint", fake_randint)

    height = 40
    d = m.new_drop(x=3, height=height)

    assert d.x == 3
    assert -height <= d.y <= 0
    assert 10.0 <= d.speed <= 15.0
    assert d.length >= max(4, height // 4)
    assert d.trail.maxlen == d.length
    assert isinstance(d.trail, deque)


def test_init_drops_calls_new_drop_for_each_x(monkeypatch: MonkeyPatch) -> None:
    created: list[tuple[int, int]] = []

    def fake_new_drop(x: int, height: int) -> m.Drop:
        created.append((x, height))
        return m.Drop(x=x, y=0.0, speed=1.0, length=5, trail=deque(maxlen=5))

    monkeypatch.setattr(m, "new_drop", fake_new_drop)

    drops = m.init_drops(width=7, height=11)
    assert len(drops) == 7
    assert created == [(x, 11) for x in range(7)]


def test_pick_color_id_non_rainbow() -> None:
    s = make_state(tail_pair=(4, "Blue"))
    assert m.pick_color_id(s) == 4


def test_pick_color_id_rainbow(monkeypatch: MonkeyPatch) -> None:
    def fake_choice(_seq: object) -> int:
        return 6

    s = make_state(tail_pair=(9, "Rainbow"))
    monkeypatch.setattr(m.random, "choice", fake_choice)
    assert m.pick_color_id(s) == 6


def test_rainbow_recolor_all_recolors_existing_trails(monkeypatch: MonkeyPatch) -> None:
    def fake_choice(_seq: object) -> int:
        return 8

    digit_colors = {i: (i, f"c{i}") for i in range(1, 9)}
    d1 = m.Drop(
        x=0,
        y=0.0,
        speed=1.0,
        length=3,
        trail=deque([(1, "A", 2), (2, "B", 2)], maxlen=3),
    )
    d2 = m.Drop(
        x=1,
        y=0.0,
        speed=1.0,
        length=3,
        trail=deque([(3, "C", 2)], maxlen=3),
    )
    s = make_state(drops=[d1, d2], digit_colors=digit_colors, tail_pair=(9, "Rainbow"))

    monkeypatch.setattr(m.random, "choice", fake_choice)

    m.rainbow_recolor_all(s)

    for d in s.drops:
        for _row, _sym, color_id in d.trail:
            assert color_id in {2, 3, 4, 5, 6, 7, 8}


def test_handle_input_quit() -> None:
    stdscr: WindowLike = FakeWindow(keys=[ord("q")])
    s = make_state()
    assert m.handle_input(stdscr, s) is False


def test_handle_input_speed_digit_0_sets_10() -> None:
    stdscr: WindowLike = FakeWindow(keys=[ord("0")])
    s = make_state(speed_mul=1.0)
    assert m.handle_input(stdscr, s) is True
    assert s.speed_mul == 10


def test_handle_input_speed_digit_7_sets_7() -> None:
    stdscr: WindowLike = FakeWindow(keys=[ord("7")])
    s = make_state(speed_mul=1.0)
    assert m.handle_input(stdscr, s) is True
    assert s.speed_mul == 7


def test_handle_input_toggle_bold() -> None:
    stdscr: WindowLike = FakeWindow(keys=[ord("b"), ord("B")])
    s = make_state(bold_front=False)

    assert m.handle_input(stdscr, s) is True
    assert s.bold_front is True

    assert m.handle_input(stdscr, s) is True
    assert s.bold_front is False


def test_handle_resize_resets_drops_when_size_changes(monkeypatch: MonkeyPatch) -> None:
    def fake_init_drops(w: int, h: int) -> list[object]:
        return ["DROPS", w, h]

    stdscr = FakeWindow(h=10, w=10)
    placeholder_drops = cast(list[m.Drop], [object()])
    s = make_state(height=10, width=10, drops=placeholder_drops)

    monkeypatch.setattr(m, "init_drops", fake_init_drops)

    stdscr.setmaxyx(12, 8)
    m.handle_resize(stdscr, s)

    assert (s.height, s.width) == (12, 8)
    assert s.drops == ["DROPS", 8, 12]
    assert ("erase",) in stdscr.calls


def test_tick_time_updates_last_and_caps_dt(monkeypatch: MonkeyPatch) -> None:
    def fake_perf_counter() -> float:
        return 1.5

    monkeypatch.setattr(m.time, "perf_counter", fake_perf_counter)
    s = make_state(last=1.0)

    dt = m.tick_time(s)

    assert dt == 0.1
    assert s.last == 1.5


def test_update_and_draw_writes_new_symbols_and_clears_tail(monkeypatch: MonkeyPatch) -> None:
    def fake_choice(_seq: object) -> str:
        return "X"

    stdscr = FakeWindow(h=6, w=2)

    monkeypatch.setattr(m.random, "choice", fake_choice)

    d = m.Drop(x=0, y=0.0, speed=10.0, length=2, trail=deque(maxlen=2))
    s = make_state(
        height=6,
        width=2,
        drops=[d],
        speed_mul=1.0,
        has_colors=False,
        bold_front=False,
    )

    m.update_and_draw(stdscr, s, dt=0.2)

    wrote = [
        (y, x, ch)
        for (name, y, x, ch, _attr) in stdscr.calls
        if name == "addch" and ch != " "
    ]
    assert (1, 0, "X") in wrote
    assert (2, 0, "X") in wrote
    assert len(d.trail) == 2

    stdscr.calls.clear()
    m.update_and_draw(stdscr, s, dt=0.2)

    erased = [
        (y, x, ch)
        for (name, y, x, ch, _attr) in stdscr.calls
        if name == "addch" and ch == " "
    ]
    assert erased, "Ожидали очистку хвоста пробелом при переполнении deque(maxlen=2)"

    wrote2 = [
        (y, x, ch)
        for (name, y, x, ch, _attr) in stdscr.calls
        if name == "addch" and ch != " "
    ]
    assert (3, 0, "X") in wrote2
    assert (4, 0, "X") in wrote2


def test_handle_input_color_switch_calls_rainbow_recolor(monkeypatch: MonkeyPatch) -> None:
    called = {"n": 0}

    def fake_rainbow_recolor_all(_s: m.State) -> None:
        called["n"] += 1

    stdscr: WindowLike = FakeWindow(keys=[ord("*")])
    digit_colors = {
        ord("!"): (2, "Green"),
        ord("*"): (9, "Rainbow"),
    }
    s = make_state(
        has_colors=True,
        digit_colors=digit_colors,
        tail_pair=digit_colors[ord("!")],
    )

    monkeypatch.setattr(m, "rainbow_recolor_all", fake_rainbow_recolor_all)

    assert m.handle_input(stdscr, s) is True
    assert s.tail_pair == (9, "Rainbow")
    assert called["n"] == 1