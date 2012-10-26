try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from urwid import Edit, ExitMainLoop
from cmd2 import Cmd

from ccli.history import History

class CommandEdit(Edit):
    def __init__(self, board, *args, **kwargs):
        super(CommandEdit, self).__init__(*args, **kwargs)
        self.board = board

        self.stdout = StringIO()
        self.cmd = Cmd(stdout=self.stdout)

        self.history = History()
        self.mapping = {
            'up': self.previous,
            'down': self.next,
            'ctrl r': self.search,
            'tab': self.autocomplete,
            'enter': self.do,
        }

    def keypress(self, size, key):
        return self.mapping.get(key, lambda: super(CommandEdit, self).keypress(size, key))()

    def previous(self):
        self.set_edit_text(self.history.up() or '')
    def next(self):
        self.set_edit_text(self.history.down() or '')

    def search(self):
        position = self.edit_pos
        query = self.edit_text[:self.edit_pos]
        result = self.history.search(query)

        if result:
            self.edit_text = result
            self.edit_pos = position

    def autocomplete(self):
        line = self.edit_text
        parsed = self.cmd.parsed(line)
        self.board.base_widget.set_text(parsed.parsed.dump())

    def do(self):
        line = self.edit_text
        stop = self.cmd.onecmd(line)
        if stop:
            raise ExitMainLoop()

        self.stdout.reset()
        self.board.base_widget.set_text(self.stdout.read())
        self.stdout.truncate()

        self.set_edit_text(u'')
        self.history.append(line)
