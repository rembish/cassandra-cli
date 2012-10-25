import curses

from ccli.client import Client

class Gui(object):
    def __init__(self, verbose=0, **kwargs):
        self.client = Client(**kwargs)
        self.screen = None

        self.command_line = None

    def __call__(self):
        curses.wrapper(self.run)

    def run(self, stdscr):
        self.screen = stdscr
        self.screen.keypad(1)

        curses.use_default_colors()
        curses.init_pair(1, -1, -1);
        curses.init_pair(2, curses.COLOR_YELLOW, -1);
        curses.init_pair(3, curses.COLOR_GREEN, -1);
        curses.init_pair(4, curses.COLOR_CYAN, -1);
        curses.init_pair(5, curses.COLOR_MAGENTA, -1);
        curses.init_pair(6, curses.COLOR_RED, -1);

        maxy, maxx = self.screen.getmaxyx()

        self.command_line = curses.newwin(10, 10, 10, 10)
        self.command_line.box()
        self.command_line.refresh()
        self.screen.refresh()

        while True:
            try:
                event = self.screen.getch()
            except KeyboardInterrupt:
                break

            if event == curses.KEY_F10:
                break

            #self.screen.move(0, 1)
            self.screen.addstr(str(event))

