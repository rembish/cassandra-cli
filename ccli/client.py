from sys import stderr

from pycassa import SystemManager, ConnectionPool, InvalidRequestException
from thrift.transport.TTransport import TTransportException

class Client(object):
    def __init__(self, host='localhost', port=9160, keyspace=None, username=None, password=None, timeout=0.5):
        credentials=None
        if username:
            credentials = {'username': username, 'password': password}

        try:
            self.manager = SystemManager('%s:%d' % (host, port), credentials=credentials)
        except TTransportException:
            print >>stderr, "ERROR: Can't connect to %s" % (
                'local Cassandra server' if host in ['localhost', '127.0.0.1']
                else "Cassandra server on '%s'" % host
            )
            exit()

        self.pool = None
        if keyspace:
            try:
                self.pool = ConnectionPool(
                    keyspace, server_list=['%s:%d' % (host, port)],
                    credentials=credentials, timeout=timeout
                )
            except InvalidRequestException:
                print >>stderr, "ERROR: Unknown keyspace '%s'" % keyspace
                exit()
