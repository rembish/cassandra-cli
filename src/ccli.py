#! /usr/bin/python
from cmd2 import Cmd
from prettytable import PrettyTable
from pyparsing import Word, Keyword, Optional, Combine, printables, alphanums, nums

from thrift.transport.TTransport import TTransportException
from pycassa.system_manager import SystemManager
from pycassa.cassandra.ttypes import NotFoundException
from pycassa.columnfamily import ColumnFamily
from pycassa.pool import ConnectionPool

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

server = Word(printables).setName('Server')
keyspace = AutoCompleteWord(printables).setName('Keyspace')
columnfamily = AutoCompleteWord(alphanums).setName('ColumnFamily')
key = Word(printables, excludeChars=':]').setName('Key')
count = Word(nums).setName('count')

class CCli(Cmd, object):
    prompt = '> '
    continuation_prompt = '. '
    
    timing = True
    colors = True
    debug = True

    # O'Key, guys, you created good library with a lot of parameters, but,
    # I think, you should test it before release, shouldn't?
    case_insensitive = False

    max_data_size = 35
    max_rows = 50
    
    def __init__(self, *args, **kwargs):
        super(CCli, self).__init__(*args, **kwargs)

        self.sm = None
        self.pool = None

        self.server = None
        self.keyspace = None

        self.settable['max_data_size'] = 'Maximum value symbols [0 = no truncating]'
        self.settable['max_rows'] = 'Maximum rows to receive by one get'

    def func_named(self, arg):
        return super(CCli, self).func_named(arg[0])

    @parse(Optional(server, default='locahost:9160'))
    def do_connect(self, server):
        try:
            self.sm = SystemManager(server)
        except TTransportException:
            return self.perror('Can not connect to %s' % server)
        
        self.server = server
        self.prompt = '%s> ' % server

        self.keyspace = None
        self.pool = None

        print 'Successfully connected to %s' % server

    @check_connection
    @parse(keyspace)
    def do_use(self, keyspace):
        if keyspace not in self.sm.list_keyspaces():
            return self.perror('Unknown keyspace %s' % keyspace)

        self.prompt = '%s/%s> ' % (self.server, keyspace)
        self.keyspace = keyspace
        self.pool = ConnectionPool(keyspace, server_list=[self.server])
        
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
        self.pfeedback([text, line, begidx, endidx])
        return [x for x in ['keyspace', 'columnfamily'] if x.startswith(text)]

    def completenames(self, text, *ignored):
        names = super(CCli, self).completenames(text, *ignored)
        if self.keyspace:
            names.extend(cf for cf in
                self.sm.get_keyspace_column_families(self.keyspace).keys()
                if cf.startswith(text))

        return names

    def default(self, line):
        # Ugly, ugly things...
        line = (' '.join(line.parsed)).strip()

        if not self.server and not self.keyspace:
            return super(CCli, self).default(line)
        return self.simple_select(line)

    @parse(columnfamily + Optional('[' + Combine(Optional(key, default='') +
        Optional(':' + Optional(key, default='') + Optional(':' +
        Optional(count, default='')))) + ']')
    )
    def simple_select(self, columnfamily, *args):
        slice = ['', '', self.max_rows]
        key = None
    
        if args and args[1]:
            if ':' not in args[1]:
                key = args[1]
            for i, part in enumerate(args[1].split(':', 2)):
                slice[i] = part

        try:
            cf = ColumnFamily(self.pool, columnfamily)
        except NotFoundException:
            return super(CCli, self).default(' '.join([columnfamily] + list(args)))

        if key:
            pt = PrettyTable(['Key', key])
            pt.set_field_align("Key", "l")
            pt.set_field_align(key, 'r')

            for k, v in cf.get(key).items():
                pt.add_row([k, (v[:self.max_data_size - 3] + '...' if self.max_data_size and len(v) > self.max_data_size else v)])

            return pt.printt(sortby='Key')

        print slice
        data = dict(cf.get_range(start=slice[0], finish=slice[1], row_count=int(slice[2])))

        columns = []
        for key, row in data.items():
            columns.extend(row.keys())
        columns = list(set(columns))
        columns.sort()

        pt = PrettyTable(['Key / Column'] + columns)
        pt.set_field_align("Key / Column", "l")
        for column in columns:
            pt.set_field_align(column, "r")

        for key, row in data.items():
            prow = [key]
            for column in columns:
                value = row.get(column, '---')
                if len(value) > self.max_data_size:
                    value = value[:self.max_data_size - 3] + '...'
                    
                prow.CCliend(value)
            pt.add_row(prow)

        pt.printt(sortby='Key / Column')

if __name__ == '__main__':
    CCli().cmdloop()
