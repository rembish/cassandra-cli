from urwid import AttrWrap, Text, WidgetWrap, Filler, Columns

class Variant(AttrWrap):
    def __init__(self, parent, token, attr, focus_attr=None, **kwargs):
        super(Variant, self).__init__(Text(token.keyword, **kwargs), attr, focus_attr=focus_attr)
        self.token = token
        self.parent = parent

    def keypress(self, size, key):
        if key in ['tab', 'shift tab']:
            k = 1 if key == 'tab' else -1
            columns = self.parent._w.original_widget
            columns.focus_position = (columns.focus_position + k) % len(columns.widget_list)
            return

        if key == 'enter':
            self.parent.result = self.token.keyword
        if key == ' ':
            self.parent.result = self.token.keyword
            if self.token.keyword[-1] != ' ' and self.token.type != 'function':
                self.parent.result += ' '

        self.parent._emit('hide_autocomplete', size, key)

class AutocompletePopup(WidgetWrap):
    signals = ['hide_autocomplete']
    _selectable = False

    def __init__(self, variants):
        super(AutocompletePopup, self).__init__(Filler(Columns([
            (15, Variant(self, word, 'complete', focus_attr='complete_selected')) for word in variants
        ])))
        self.result = None
