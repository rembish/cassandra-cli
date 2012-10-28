from pycassa import SystemManager, ConnectionPool, InvalidRequestException
from thrift.transport.TTransport import TTransportException

from ccli.errors import CCliClientConnectionError, CCliClientKeyspaceError

class Client(object):
    def __init__(self, host='localhost', port=9160, keyspace=None, username=None, password=None, timeout=0.5):
        self.credentials = None
        self.timeout = timeout

        if username:
            self.credentials = {'username': username, 'password': password}

        self.server = '%s:%s' % (host, port)

        self.pool = None
        if keyspace:
            self.keyspace = keyspace

    def set_keyspace(self, keyspace):
        try:
            self.pool = ConnectionPool(
                keyspace, server_list=[self.manager._conn.server],
                credentials=self.credentials, timeout=self.timeout
            )
        except InvalidRequestException:
            raise CCliClientKeyspaceError("Unknown keyspace '%s'" % keyspace)
    keyspace = property(lambda self: self.pool and self.pool.keyspace, set_keyspace)

    def set_server(self, server):
        try:
            self.manager = SystemManager(server, credentials=self.credentials)
        except TTransportException:
            host = server.split(':')[0]
            raise CCliClientConnectionError("Can't connect to %s" % (
                'local Cassandra server' if host in ['localhost', '127.0.0.1']
                else "Cassandra server on '%s'" % host
            ))
    server = property(lambda self: self.manager._conn.server, set_server)

    @property
    def caption(self):
        if self.pool:
            return '%s/%s' % (self.manager._conn.server, self.pool.keyspace)
        return self.manager._conn.server
