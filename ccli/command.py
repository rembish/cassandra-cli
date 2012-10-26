from cStringIO import StringIO
from pyreadline import Readline

from cmd2 import Cmd
from ccli.oldcli import CCli
from urwid import Edit, ExitMainLoop

class CommandEdit(Edit):
    def __init__(self, board, *args, **kwargs):
        super(CommandEdit, self).__init__(*args, **kwargs)
        self.board = board

        self.readline = Readline()
        self.readline.set_completer(self.complete)
        self.readline.parse_and_bind('tab: complete')

        self.stdout = StringIO()
        self.cmd = Cmd(stdout=self.stdout)

    def complete(self, text, state):
        return map(str, [text, state])

    def keypress(self, size, key):
        if key not in ['enter', 'tab']:
            return super(CommandEdit, self).keypress(size, key)

        line = self.get_edit_text()
        if key == 'tab':
            variants = self.cmd.complete(line, state=0)
            self.board.base_widget.set_text(', '.join(variants or []) or '')
            return

        stop = self.cmd.onecmd(line)
        if stop:
            raise ExitMainLoop()

        self.stdout.reset()
        self.board.base_widget.set_text(self.stdin.read())

        self.set_edit_text(u'')
