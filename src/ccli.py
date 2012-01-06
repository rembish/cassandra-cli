from cmd2 import Cmd
from prettytable import PrettyTable
from pyparsing import Word, Keyword, Optional, printables

from thrift.transport.TTransport import TTransportException
from pycassa.system_manager import SystemManager
from pycassa.cassandra.ttypes import NotFoundException

class AutoCompleteWord(Word):
    pass

def check(grammar):
    def decorator(function):
        def proxy(self, line):
            result = grammar.parseString(line)
            return function(self, *result)

        return proxy
    return decorator

server = Word(printables).setName('server')
keyspace = AutoCompleteWord(printables).setName('keyspace')
columnfamily = AutoCompleteWord(printables).setName('columnfamily')

class App(Cmd, object):
    prompt = '> '
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        self.sm = None
        self.servers = []
        self.keyspace = None

    @check(Optional(server, default='locahost:9160'))
    def do_connect(self, server):
        try:
            self.sm = SystemManager(server)
        except TTransportException:
            print '*** Can not connect to %s' % server
            return
        
        self.servers = [server]
        self.prompt = '%s> ' % server
        print 'Successfully connected to %s' % server

    @check(keyspace)
    def do_use(self, keyspace):
        if not self.sm:
            print '*** Please connect to server'
            return

        if keyspace not in self.sm.list_keyspaces():
            print '*** Unknown keyspace %s' % keyspace
            return

        self.prompt = '%s/%s> ' % (self.servers[0], keyspace)
        self.keyspace = keyspace

    def complete_use(self, text, line, begidx, endidx):
        if not self.sm:
            return []
        
        return [x for x in self.sm.list_keyspaces() if x.startswith(text)]

    @check(Keyword('keyspaces') | Keyword('columnfamilies'))
    def do_list(self, space):
        if not self.sm:
            print '*** Please, connect to server'
            return

        if space == 'keyspaces':
            pt = PrettyTable(['Keyspaces'])
            pt.set_field_align("Keyspaces", "l")

            for ks in self.sm.list_keyspaces():
                pt.add_row([ks])

            pt.printt(sortby="Keyspaces")

        elif space == 'columnfamilies':
            if not self.keyspace:
                print '*** Please, select keyspace, using "use" command'
                return

            pt = PrettyTable(['ColumnFamilies'])
            pt.set_field_align("ColumnFamilies", "l")

            for cf in self.sm.get_keyspace_column_families(self.keyspace).keys():
                pt.add_row([cf])

            pt.printt(sortby="ColumnFamilies")

    def complete_list(self, text, line, begidx, endidx):
        return [x for x in ['keyspaces', 'columnfamilies'] if x.startswith(text)]

    @check(Keyword('keyspace') + Optional(keyspace, default=None) | Keyword('columnfamily') + columnfamily)
    def do_describe(self, space, name):
        if not self.sm:
            print '*** Please, connect to server'
            return

        if space == 'keyspace':
            if not name and not self.keyspace:
                print '*** Please, define keyspace'
                return

            keyspace = name or self.keyspace
            try:
                options = self.sm.get_keyspace_properties(keyspace)
            except NotFoundException:
                print '*** Unknown keyspace %s' % keyspace
                return
            
            pt = PrettyTable(['Keyspace', keyspace])
            pt.set_field_align("Keyspace", "l")
            pt.set_field_align(keyspace, 'r')

            pt.add_row(['replication_strategy', options['replication_strategy']])
            for k, v in options['strategy_options'].items():
                pt.add_row([k, v])

            pt.printt(sortby='Keyspace')

        elif space == 'columnfamily':
            if not self.keyspace:
                print '*** Please, select keyspace, using "use" command'
                return

            try:
                options = self.sm.get_keyspace_column_families(self.keyspace, use_dict_for_col_metadata=True)[name]
            except KeyError:
                print '*** Unknown columnfamily %s' % name
                return

            pt = PrettyTable(['ColumnFamily', name])
            pt.set_field_align("ColumnFamily", "l")
            pt.set_field_align(name, 'r')

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

App().cmdloop()
