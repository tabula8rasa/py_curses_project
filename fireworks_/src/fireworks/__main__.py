import curses
from fireworks.app import run

if __name__ == "__main__":
    curses.wrapper(run)