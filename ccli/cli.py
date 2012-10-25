from optparse import OptionParser
from getpass import getpass
from sys import version_info, argv

from pycassa import __version__ as pycassa_version

from ccli import __version__ as ccli_version
from ccli.gui import Gui

def process_password(option, opt_str, value, parser):
    if parser.rargs and not parser.rargs[0].startswith('-'):
        v = parser.rargs[0]
        parser.rargs.pop(0)
    else:
        v = getpass('Enter password: ')

    setattr(parser.values, option.dest, v)

def main(args=argv[1:]):
    parser = OptionParser(
        version='cassandra-cli/%s (using pycassa/%s, Python/%s)' % (
            ccli_version, pycassa_version, '.'.join(map(str, version_info[:3]))
            ),
        usage='Usage: %prog [OPTIONS] [keyspace]',
        description='Cassanda Command-Line Interface',
        add_help_option=False
    )

    parser.remove_option('--version')
    parser.add_option('-?', '--help', dest='show_help', help='Display this help and exit.', action='store_true', default=False)
    parser.add_option('-I', dest='show_help', help='Synonym for -?', action='store_true')
    parser.add_option('-V', '--version', dest='show_version', help='Output version information and exit.', action='store_true', default=False)
    parser.add_option('-v', '--verbose', dest='verbose', help='Write more.', metavar='verbose', action='count', default=0)

    parser.add_option('-h', '--host', dest='host', help='Connect to host.', metavar='name', default='localhost')
    parser.add_option('-P', '--port', dest='port', help='Port number to use for connection (default: %default).', metavar='#', default=9160, type='int')

    parser.add_option('-u', '--user', dest='username', help='User for login', metavar='name', default=None)
    parser.add_option('-p', '--password', dest='password', help="Password to use when connecting to server. If password is not given it's asked from the tty.", metavar='name', default=None, action='callback', callback=process_password)

    parser.add_option('-k', '--keyspace', dest='keyspace', help='Keyspace to use.', metavar='name', default=None)
    parser.add_option('-d', '--database', dest='keyspace', help='Synonym for -k (mysql client compatibility).', metavar='name')

    parser.add_option('--connect-timeout', dest='timeout', help='Number of seconds before connection timeout.', metavar='#', default=0.5, type='float')

    options, args = parser.parse_args(args=args)
    if len(args) == 1:
        options.keyspace = args[0]

    if options.show_help or len(args) > 1:
        parser.print_version()
        parser.print_help()
    elif options.show_version:
        parser.print_version()
    else:
        try:
            Gui(
                host=options.host, port=options.port, keyspace=options.keyspace,
                username=options.username, password=options.password, timeout=options.timeout,
                verbose=options.verbose
            )()
        except Exception as e:
            if options.verbose >= 2:
                raise

            print 'CCLI ERROR: %s' % str(e)

if __name__ == '__main__':
    main(argv)
