from cmd2 import Cmd
from prettytable import PrettyTable
from pyparsing import Word, Keyword, Optional, printables

from thrift.transport.TTransport import TTransportException
from pycassa.system_manager import SystemManager
from pycassa.cassandra.ttypes import NotFoundException

class AutoCompleteWord(Word):
    pass

def parse(grammar):
    def decorator(function):
        def proxy(self, line):
            result = grammar.parseString(line)
            return function(self, *result)

        return proxy
    return decorator

def check_connection(function):
    def proxy(self, *args):
        if not self.server:
            return self.perror('Please, connect to cassandra server')
        return function(self, *args)
    return proxy

def check_keyspace(function):
    def proxy(self, *args):
        if not self.keyspace:
            return self.perror('Please, select working keyspace')
        return function(self, *args)
    return proxy

server = Word(printables).setName('server')
keyspace = AutoCompleteWord(printables).setName('keyspace')
columnfamily = AutoCompleteWord(printables).setName('columnfamily')

class App(Cmd, object):
    prompt = '> '
    timing = True
    
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        self.sm = None
        self.server = None
        self.keyspace = None

    @parse(Optional(server, default='locahost:9160'))
    def do_connect(self, server):
        try:
            self.sm = SystemManager(server)
        except TTransportException:
            return self.perror('Can not connect to %s' % server)
        
        self.server = server
        self.prompt = '%s> ' % server
        print 'Successfully connected to %s' % server

    @check_connection
    @parse(keyspace)
    def do_use(self, keyspace):
        if keyspace not in self.sm.list_keyspaces():
            return self.perror('Unknown keyspace %s' % keyspace)

        self.prompt = '%s/%s> ' % (self.server, keyspace)
        self.keyspace = keyspace
        print 'Using %s as default keyspace' % keyspace

    def complete_use(self, text, line, begidx, endidx):
        if not self.sm:
            return []
        
        return [x for x in self.sm.list_keyspaces() if x.startswith(text)]

    @check_connection
    @parse(Keyword('keyspaces') | Keyword('columnfamilies'))
    def do_list(self, space):
        return getattr(self, 'list_%s' % space)()

    def list_keyspaces(self):
        pt = PrettyTable(['Keyspaces'])
        pt.set_field_align("Keyspaces", "l")

        for ks in self.sm.list_keyspaces():
            pt.add_row([ks])

        pt.printt(sortby="Keyspaces")

    @check_keyspace
    def list_columnfamilies(self):
        pt = PrettyTable(['ColumnFamilies'])
        pt.set_field_align("ColumnFamilies", "l")

        for cf in self.sm.get_keyspace_column_families(self.keyspace).keys():
            pt.add_row([cf])

        pt.printt(sortby="ColumnFamilies")

    def complete_list(self, text, line, begidx, endidx):
        return [x for x in ['keyspaces', 'columnfamilies'] if x.startswith(text)]

    @check_connection
    @parse(Keyword('keyspace') + Optional(keyspace, default=None) | Keyword('columnfamily') + columnfamily)
    def do_describe(self, space, name):
        return getattr(self, 'describe_%s' % space)(name)

    def describe_keyspace(self, keyspace):
        keyspace = keyspace or self.keyspace
        if not keyspace:
            return self.perror('Please, select working keyspace or define it as command parameter')

        try:
            options = self.sm.get_keyspace_properties(keyspace)
        except NotFoundException:
            return self.perror('Unknown keyspace %s' % keyspace)

        pt = PrettyTable(['Keyspace', keyspace])
        pt.set_field_align("Keyspace", "l")
        pt.set_field_align(keyspace, 'r')

        pt.add_row(['replication_strategy', options['replication_strategy']])
        for k, v in options['strategy_options'].items():
            pt.add_row([k, v])

        pt.printt(sortby='Keyspace')

    @check_keyspace
    def describe_columnfamily(self, columnfamily):
        try:
            options = self.sm.get_keyspace_column_families(self.keyspace, use_dict_for_col_metadata=True)[columnfamily]
        except KeyError:
            return self.perror('Unknown columnfamily %s' % columnfamily)

        pt = PrettyTable(['ColumnFamily', columnfamily])
        pt.set_field_align("ColumnFamily", "l")
        pt.set_field_align(columnfamily, 'r')

        for k, v in options.__dict__.items():
            if k == 'column_metadata' and len(v):
                continue
            pt.add_row([k, v])

        pt.printt(sortby='ColumnFamily')

        if len(options.column_metadata):
            pt = PrettyTable(['Column \ Options'] + options.column_metadata.values()[0].__dict__.keys())

            for k, v in options.column_metadata.items():
                pt.add_row([k] + v.__dict__.values())

            pt.printt(sortby='Column \ Options')

    def complete_describe(self, text, line, begidx, endidx):
        return [x for x in ['keyspace', 'columnfamily'] if x.startswith(text)]

if __name__ == '__main__':
    App().cmdloop()
