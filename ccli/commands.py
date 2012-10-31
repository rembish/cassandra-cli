from cmd import Cmd
from urwid import ExitMainLoop

from ccli.errors import CCliClientKeyspaceError
#from ccli.grammar import use_statement

def parse(grammar):
    def decorator(function):
        def proxy(self, line):
            result = grammar.parseString('%s %s' % (function.__name__[3:], line))
            return function(self, *result[1:])

        return proxy
    return decorator

class CommandsMixin(Cmd):
    def __init__(self, client, *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)
        self.client = client

    def do_quit(self, arg):
        raise ExitMainLoop()
    do_exit = do_quit

    #@parse(use_statement)
    def do_use(self, keyspace):
        try:
            self.client.keyspace = keyspace
            self.set_caption('%s> ' % self.client.caption)
            return ''
        except CCliClientKeyspaceError as e:
            return str(e)

    def completedefault(self, *words):
        self.board.base_widget.set_text(repr(words))
        return []