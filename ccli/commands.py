from cmd import Cmd
from urwid import ExitMainLoop

from ccli.errors import CCliClientKeyspaceError

class CommandsMixin(Cmd):
    def __init__(self, client, *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)
        self.client = client

    def do_quit(self, arg):
        raise ExitMainLoop()
    do_exit = do_quit

    def do_use(self, keyspace):
        try:
            self.client.keyspace = keyspace
            self.set_caption('%s> ' % self.client.caption)
            return ''
        except CCliClientKeyspaceError as e:
            return str(e)