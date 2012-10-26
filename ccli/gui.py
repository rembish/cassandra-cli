from ccli.client import Client
from urwid import MainLoop, Frame, Text, ExitMainLoop, Filler, Pile, Divider
from ccli.command import CommandEdit

class Gui(object):
    def __init__(self, verbose=0, **kwargs):
        self.client = Client(**kwargs)

    @property
    def caption(self):
        return '%s> ' % self.client.caption

    def run(self):
        board = Filler(Text(u''), valign='top')
        footer = Pile([
            Divider(div_char=u'\u2500'),
            CommandEdit(caption=self.caption, board=board)
        ], focus_item=1)
        screen = Frame(board, footer=footer, focus_part='footer')

        try:
            MainLoop(screen).run()
        except KeyboardInterrupt:
            pass
