# test_matrix_rain.py
# Запуск: pytest -q
#
# ВАЖНО:
# 1) Положи свой код в файл, например matrix_rain.py
# 2) Если имя файла другое — поменяй IMPORT ниже.
#
# Эти тесты не требуют реального терминала/curses-инициализации:
# мы используем фейковое окно и, где нужно, отключаем has_colors.

import types
from collections import deque

import pytest

import pmatrix as m  # <-- поменяй на имя своего файла (без .py)


class FakeCursesError(Exception):
    pass


class FakeWindow:
    """Минимальная заглушка curses.window, которая записывает вызовы."""
    def __init__(self, h=24, w=80, keys=None):
        self._h = h
        self._w = w
        self._keys = list(keys) if keys is not None else []
        self.calls = []  # список кортежей ("method", args...)

    def getmaxyx(self):
        return self._h, self._w

    def setmaxyx(self, h, w):
        self._h, self._w = h, w

    def getch(self):
        if not self._keys:
            return -1
        return self._keys.pop(0)

    def erase(self):
        self.calls.append(("erase",))

    def addch(self, y, x, ch, attr=0):
        self.calls.append(("addch", y, x, ch, attr))

    def addstr(self, y, x, s):
        self.calls.append(("addstr", y, x, s))

    def nodelay(self, flag):
        self.calls.append(("nodelay", flag))

    def keypad(self, flag):
        self.calls.append(("keypad", flag))

    def bkgd(self, ch, attr):
        self.calls.append(("bkgd", ch, attr))

    def refresh(self):
        self.calls.append(("refresh",))


def make_state(
    *,
    height=10,
    width=5,
    drops=None,
    speed_mul=1.0,
    has_colors=False,
    tail_pair=(2, "Green"),
    digit_colors=None,
    bold_front=False,
    FPS=120,
    frame_ms=8,
    last=0.0,
):
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


def test_new_drop_ranges(monkeypatch):
    # делаем random детерминированным
    monkeypatch.setattr(m.random, "uniform", lambda a, b: (a + b) / 2)
    monkeypatch.setattr(m.random, "randint", lambda a, b: a)  # минимум

    height = 40
    d = m.new_drop(x=3, height=height)

    assert d.x == 3
    assert -height <= d.y <= 0
    assert 10.0 <= d.speed <= 15.0
    assert d.length >= max(4, height // 4)
    assert d.trail.maxlen == d.length
    assert isinstance(d.trail, deque)


def test_init_drops_calls_new_drop_for_each_x(monkeypatch):
    created = []

    def fake_new_drop(x, height):
        created.append((x, height))
        return m.Drop(x=x, y=0.0, speed=1.0, length=5, trail=deque(maxlen=5))

    monkeypatch.setattr(m, "new_drop", fake_new_drop)

    drops = m.init_drops(width=7, height=11)
    assert len(drops) == 7
    assert created == [(x, 11) for x in range(7)]


def test_pick_color_id_non_rainbow():
    s = make_state(tail_pair=(4, "Blue"))
    assert m.pick_color_id(s) == 4


def test_pick_color_id_rainbow(monkeypatch):
    s = make_state(tail_pair=(9, "Rainbow"))
    monkeypatch.setattr(m.random, "choice", lambda seq: 6)
    assert m.pick_color_id(s) == 6


def test_rainbow_recolor_all_recolors_existing_trails(monkeypatch):
    # digit_colors: 8 клавиш => palette 2..8
    digit_colors = {i: (i, f"c{i}") for i in range(1, 9)}
    d1 = m.Drop(x=0, y=0.0, speed=1.0, length=3, trail=deque([(1, "A", 2), (2, "B", 2)], maxlen=3))
    d2 = m.Drop(x=1, y=0.0, speed=1.0, length=3, trail=deque([(3, "C", 2)], maxlen=3))
    s = make_state(drops=[d1, d2], digit_colors=digit_colors, tail_pair=(9, "Rainbow"))

    # пусть всегда выбирается 8
    monkeypatch.setattr(m.random, "choice", lambda seq: 8)

    m.rainbow_recolor_all(s)

    for d in s.drops:
        for row, sym, color_id in d.trail:
            assert color_id in {2, 3, 4, 5, 6, 7, 8}


def test_handle_input_quit():
    stdscr = FakeWindow(keys=[ord("q")])
    s = make_state()
    assert m.handle_input(stdscr, s) is False


def test_handle_input_speed_digit_0_sets_10():
    stdscr = FakeWindow(keys=[ord("0")])
    s = make_state(speed_mul=1.0)
    assert m.handle_input(stdscr, s) is True
    assert s.speed_mul == 10


def test_handle_input_speed_digit_7_sets_7():
    stdscr = FakeWindow(keys=[ord("7")])
    s = make_state(speed_mul=1.0)
    assert m.handle_input(stdscr, s) is True
    assert s.speed_mul == 7


def test_handle_input_toggle_bold():
    stdscr = FakeWindow(keys=[ord("b"), ord("B")])
    s = make_state(bold_front=False)

    assert m.handle_input(stdscr, s) is True
    assert s.bold_front is True

    assert m.handle_input(stdscr, s) is True
    assert s.bold_front is False


def test_handle_resize_resets_drops_when_size_changes(monkeypatch):
    stdscr = FakeWindow(h=10, w=10)
    s = make_state(height=10, width=10, drops=[object()])

    monkeypatch.setattr(m, "init_drops", lambda w, h: ["DROPS", w, h])

    stdscr.setmaxyx(12, 8)
    m.handle_resize(stdscr, s)

    assert (s.height, s.width) == (12, 8)
    assert s.drops == ["DROPS", 8, 12]
    assert ("erase",) in stdscr.calls


def test_tick_time_updates_last_and_caps_dt(monkeypatch):
    # perf_counter вернёт 1.5. last был 1.0 => dt=0.5 => cap=0.1
    monkeypatch.setattr(m.time, "perf_counter", lambda: 1.5)
    s = make_state(last=1.0)

    dt = m.tick_time(s)

    assert dt == pytest.approx(0.1)  # capped
    assert s.last == pytest.approx(1.5)



def test_update_and_draw_writes_new_symbols_and_clears_tail(monkeypatch):
    # Отключаем colors, чтобы не зависеть от curses.color_pair
    stdscr = FakeWindow(h=6, w=2)

    # Детерминируем выбор символа
    monkeypatch.setattr(m.random, "choice", lambda seq: "X")

    # drop: длина 2, старт y=0, скорость 10
    d = m.Drop(x=0, y=0.0, speed=10.0, length=2, trail=deque(maxlen=2))
    s = make_state(height=6, width=2, drops=[d], speed_mul=1.0, has_colors=False, bold_front=False)

    # шаг 1: dt=0.2 => y=2, добавим строки 1..2
    m.update_and_draw(stdscr, s, dt=0.2)

    # Должны быть addch на (1,0,'X') и (2,0,'X') среди вызовов
    wrote = [(y, x, ch) for (name, y, x, ch, attr) in stdscr.calls if name == "addch" and ch != " "]
    assert (1, 0, "X") in wrote
    assert (2, 0, "X") in wrote
    assert len(d.trail) == 2

    # шаг 2: dt=0.2 => y=4, добавим строки 3..4,
    # при добавлении 3-го элемента хвост переполнится => должен стереться tail ' ' на старой строке
    stdscr.calls.clear()
    m.update_and_draw(stdscr, s, dt=0.2)

    # Проверяем, что хоть раз стирали пробелом
    erased = [(y, x, ch) for (name, y, x, ch, attr) in stdscr.calls if name == "addch" and ch == " "]
    assert erased, "Ожидали очистку хвоста пробелом при переполнении deque(maxlen=2)"

    # И что появились новые символы на строках 3 и 4
    wrote2 = [(y, x, ch) for (name, y, x, ch, attr) in stdscr.calls if name == "addch" and ch != " "]
    assert (3, 0, "X") in wrote2
    assert (4, 0, "X") in wrote2


def test_handle_input_color_switch_calls_rainbow_recolor(monkeypatch):
    # Проверяем, что при выборе '*' (Rainbow) вызывается rainbow_recolor_all
    called = {"n": 0}
    monkeypatch.setattr(m, "rainbow_recolor_all", lambda s: called.__setitem__("n", called["n"] + 1))

    stdscr = FakeWindow(keys=[ord("*")])
    digit_colors = {
        ord("!"): (2, "Green"),
        ord("*"): (9, "Rainbow"),
    }
    s = make_state(has_colors=True, digit_colors=digit_colors, tail_pair=digit_colors[ord("!")])

    assert m.handle_input(stdscr, s) is True
    assert s.tail_pair == (9, "Rainbow")
    assert called["n"] == 1
