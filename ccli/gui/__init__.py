from urwid import MainLoop, Frame, Text, Filler, Pile, Divider

from ccli.client import Client
from ccli.gui.commandline import CommandLineWrapper

class GUI(object):
    def __init__(self, verbose=0, **kwargs):
        self.client = Client(**kwargs)

    def run(self):
        board = Filler(Text(u''), valign='top')
        footer = Pile([
            Divider(div_char=u'\u2500'),
            CommandLineWrapper(board=board, client=self.client)
        ], focus_item=1)
        screen = Frame(board, footer=footer, focus_part='footer')

        try:
            MainLoop(screen, [
                ('complete', 'default', 'default'),
                ('complete_selected', 'default,bold', 'default')
            ], pop_ups=True).run()
        except KeyboardInterrupt:
            pass

