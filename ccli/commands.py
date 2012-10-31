from modgrammar import ParseError
from urwid import ExitMainLoop

from ccli.errors import CCliClientKeyspaceError
from ccli.grammar import Statement

class CommandsMixin:
    def __init__(self, client):
        self.client = client
        self.parser = Statement.parser()

    def _get_tokens(self, input, valid=[]):
        try:
            self.parser.reset()
            self.parser.parse_string(input, eof=True)
        except ParseError as e:
            return filter(lambda t: t.grammar_name[:2] in valid, e.expected)
        return []

    def complete(self, input, position=0):
        initial = input[:position]
        ews = initial and initial[-1] == ' '
        tokens = filter(lambda x: x, initial.split(' '))
        last = tokens.pop(-1) if tokens else None
        totest = ' '.join(tokens)

        if ews:
            return self._get_tokens(initial, ['OP', 'CK', 'FN'])

        if not tokens:
            totest = ';'

        variants = self._get_tokens(totest, ['OP', 'CK', 'FN'])
        if last:
            variants = filter(lambda t: t.keyword.startswith(last) and t.keyword != last, variants)
        variants += self._get_tokens('%s ' % initial, ['OP'])

        return variants

    def default(self, command, arguments):
        return 'Not implemented command: %s' % command.strip()

    def onecmd(self, line):
        self.parser.reset()
        try:
            tokens = self.parser.parse_string(line, eof=True).terminals()
            command = tokens[0].keyword.strip()
            return getattr(self, 'do_%s' % command)(tokens[1:])
        except ParseError as e:
            tokens = [t.keyword.strip() for t in e.expected if t.grammar_name[:2] in ['OP', 'CK', 'FN']]
            return "Syntax error:\n%s\n%s^-- Expected '%s'" % (line, ' ' * e.col, "' or '".join(
                tokens or ['name']
            ).replace(' or ', ', ', len(tokens) - 2))
        except AttributeError as e:
            return self.default(command, tokens[1:])

    def do_quit(self, args):
        raise ExitMainLoop()
    do_exit = do_quit

    def do_use(self, args):
        try:
            self.client.keyspace = args[0].string
            self.set_caption('%s> ' % self.client.caption)
            return ''
        except CCliClientKeyspaceError as e:
            return str(e)
