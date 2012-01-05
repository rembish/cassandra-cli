from cmd2 import Cmd
from prettytable import PrettyTable

from thrift.transport.TTransport import TTransportException
from pycassa.system_manager import SystemManager
from pycassa.cassandra.ttypes import NotFoundException

class App(Cmd, object):
    prompt = '> '
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        self.sm = None
        self.servers = []
        self.keyspace = None

    def do_connect(self, line):
        server = line or 'new-cass01.prague.wdf.cz' # 'localhost:9160'

        try:
            self.sm = SystemManager(server)
        except TTransportException:
            print '*** Can not connect to %s' % server
            return
        
        self.servers = [server]
        self.prompt = '%s> ' % server
        print 'Successfully connected to %s' % server

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

    def do_list(self, line):
        if not self.sm:
            print '*** Please, connect to server'
            return

        if line.startswith('keyspaces'):
            pt = PrettyTable(['Keyspaces'])
            pt.set_field_align("Keyspaces", "l")

            for ks in self.sm.list_keyspaces():
                pt.add_row([ks])

            pt.printt(sortby="Keyspaces")

        elif line.startswith('columnfamilies'):
            if not self.keyspace:
                print '*** Please, select keyspace, using "use" command'
                return

            pt = PrettyTable(['ColumnFamilies'])
            pt.set_field_align("ColumnFamilies", "l")

            for cf in self.sm.get_keyspace_column_families(self.keyspace).keys():
                pt.add_row([cf])

            pt.printt(sortby="ColumnFamilies")

        else:
            print '*** Unknown option %s' % line

    def complete_list(self, text, line, begidx, endidx):
        return [x for x in ['keyspaces', 'columnfamilies'] if x.startswith(text)]

    def do_describe(self, line):
        if not self.sm:
            print '*** Please, connect to server'
            return

        data = line.split(' ')
        if line.startswith('keyspace'):
            if len(data) < 2 and not self.keyspace:
                print '*** Please, define keyspace'
                return

            keyspace = data[1] if len(data) > 1 else self.keyspace
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

        elif line.startswith('columnfamily'):
            if not self.keyspace:
                print '*** Please, select keyspace, using "use" command'
                return

            if len(data) < 2:
                print '*** Please, define columnfamily to describe'
                return

            columnfamily = data[1]
            try:
                options = self.sm.get_keyspace_column_families(self.keyspace, use_dict_for_col_metadata=True)[columnfamily]
            except KeyError:
                print '*** Unknown columnfamily %s' % columnfamily
                return

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

        else:
            print '*** Unknown option %s' % line

    def complete_describe(self, text, line, begidx, endidx):
        return [x for x in ['keyspace', 'columnfamily'] if x.startswith(text)]

App().cmdloop()
