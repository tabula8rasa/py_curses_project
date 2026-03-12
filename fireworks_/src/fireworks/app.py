from __future__ import annotations
import curses
import random

from .config import config
from .domain.firework import Firework
from .services.randomizer import Randomizer
from .services.timer import Timer
from .ui.curses_setup import CursesSetup
from .ui.screen_mapper import ScreenMapper


def run(stdscr: curses.window) -> None:
    CursesSetup.setup_screen(stdscr)

    setup = ScreenMapper(stdscr, config)
    randomizer = Randomizer(config, random.Random())

    fireworks = [Firework(config, setup, randomizer, stdscr)]
    timer = Timer(dt=config.dt, delay=config.time_delay_to_a_new_firework)

    while True:
        timer.wait_frame()
        timer.counter += 1

        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27):
            break

        stdscr.erase()

        alive_fireworks: list[Firework] = []

        for firework in fireworks:
            firework.update_particles()
            status = firework.render_firework()
            if status:
                alive_fireworks.append(firework)

        fireworks =  alive_fireworks
            
        stdscr.refresh()

        if timer.counter == timer.delay:
            fireworks.append(Firework(config, setup, randomizer, stdscr))
            timer.counter = 0
            timer.delay = int(config.time_delay_to_a_new_firework - (randomizer.rnd.random()*(config.time_delay_to_a_new_firework//2)))
