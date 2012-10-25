from ccli.client import Client

class Gui(object):
    def __init__(self, **kwargs):
        self.client = Client(**kwargs)

    def run(self):
        pass
