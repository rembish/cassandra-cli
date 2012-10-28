try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from urwid import Edit, ExitMainLoop, PopUpLauncher, connect_signal

from ccli.history import History
from ccli.commands import CommandsMixin
from ccli.gui.autocomplete import AutocompletePopup

class CommandLineWrapper(PopUpLauncher):
    def __init__(self, *args, **kwargs):
        super(CommandLineWrapper, self).__init__(CommandLine(*args, **kwargs))

        self.variants = []
        connect_signal(self.original_widget, 'show_autocomplete', self.show)

    def show(self, _, variants):
        self.variants = variants
        return self.open_pop_up()

    def hide(self, popup, size, key):
        self.close_pop_up()

        if not getattr(popup, 'result', None):
            return self.original_widget.keypress(size, key)

        text = self.original_widget
        word = text.edit_text[:text.edit_pos].rsplit(' ')[-1]
        text.insert_text('%s ' % popup.result[len(word):])

    def create_pop_up(self):
        popup = AutocompletePopup(self.variants)
        connect_signal(popup, 'hide_autocomplete', self.hide)
        return popup

    def get_pop_up_parameters(self):
        caption_len = len(self.original_widget.caption)
        width = max(80 - caption_len, self.original_widget.pack()[0])
        return {'left': caption_len, 'top': -2, 'overlay_width': width, 'overlay_height': 1}

class CommandLine(Edit, CommandsMixin):
    signals = ['change', 'show_autocomplete']
    def __init__(self, board, client, *args, **kwargs):
        super(CommandLine, self).__init__(*args, **kwargs)

        self.stdout = StringIO()
        CommandsMixin.__init__(self, client, stdout=self.stdout)

        self.board = board
        self.client = client

        self.history = History()
        self.mapping = {
            'up': self.previous,
            'down': self.next,
            'ctrl r': self.search,
            'tab': self.autocomplete,
            'enter': self.do,
        }

    def keypress(self, size, key):
        #self.board.base_widget.set_text(key)
        return self.mapping.get(key, lambda: super(CommandLine, self).keypress(size, key))()

    def previous(self):
        self.set_edit_text(self.history.up() or '')
        self.set_edit_pos(len(self.edit_text))
    def next(self):
        self.set_edit_text(self.history.down() or '')
        self.set_edit_pos(len(self.edit_text))

    def search(self):
        position = self.edit_pos
        query = self.edit_text[:self.edit_pos]
        result = self.history.search(query)

        if result:
            self.edit_text = result
            self.edit_pos = position

    def autocomplete(self):
        result = self.complete(self.edit_text[:self.edit_pos], 0)
        if len(self.completion_matches) == 1:
            word = self.edit_text[:self.edit_pos].rsplit(' ')[-1]
            self.insert_text('%s ' % result[len(word):])
        elif self.completion_matches:
            self._emit('show_autocomplete', self.completion_matches)

    def do(self):
        line = self.edit_text
        result = self.onecmd(line)

        self.stdout.reset()
        self.board.base_widget.set_text(result)
        self.stdout.truncate()

        self.set_edit_text(u'')
        self.history.append(line)
