import curses

class CursesSetup:
    @staticmethod
    def setup_screen(stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(0)

        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            curses.init_pair(1, curses.COLOR_YELLOW, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_MAGENTA, -1)

            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_YELLOW, -1)
            curses.init_pair(6, curses.COLOR_YELLOW, -1)

            curses.init_pair(7, curses.COLOR_CYAN, -1)
            curses.init_pair(8, curses.COLOR_CYAN, -1)
            curses.init_pair(9, curses.COLOR_CYAN, -1)

            curses.init_pair(10, curses.COLOR_BLUE, -1)
            curses.init_pair(11, curses.COLOR_BLUE, -1)
            curses.init_pair(12, curses.COLOR_BLUE, -1)

            curses.init_pair(13, curses.COLOR_MAGENTA, -1)
            curses.init_pair(14, curses.COLOR_MAGENTA, -1)
            curses.init_pair(15, curses.COLOR_MAGENTA, -1)

            curses.init_pair(16, curses.COLOR_GREEN, -1)
            curses.init_pair(17, curses.COLOR_GREEN, -1)
            curses.init_pair(18, curses.COLOR_GREEN, -1)

            curses.init_pair(19, curses.COLOR_WHITE, -1)
            curses.init_pair(20, curses.COLOR_WHITE, -1)
            curses.init_pair(21, curses.COLOR_WHITE, -1)

            # Ледяной: white -> cyan -> blue
            curses.init_pair(22, curses.COLOR_WHITE, -1)
            curses.init_pair(23, curses.COLOR_CYAN, -1)
            curses.init_pair(24, curses.COLOR_BLUE, -1)

            # Фиолетовый: white -> magenta -> blue
            curses.init_pair(25, curses.COLOR_WHITE, -1)
            curses.init_pair(26, curses.COLOR_MAGENTA, -1)
            curses.init_pair(27, curses.COLOR_BLUE, -1)

            # Изумрудный: white -> green -> cyan
            curses.init_pair(28, curses.COLOR_WHITE, -1)
            curses.init_pair(29, curses.COLOR_GREEN, -1)
            curses.init_pair(30, curses.COLOR_CYAN, -1)

