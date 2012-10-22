from setuptools import setup, find_packages
from os.path import dirname, abspath, join
from ccli import __version__

readme = join(dirname(abspath(__file__)), 'README.rst')

setup(
    name='cassandra-cli',
    version=__version__,
    description='Cassandra Console Interface (MySQL client like)',
    long_description="".join(open(readme).readlines()),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cassandra-cli = ccli.cli:main',
        ]
    },
    url='https://github.com/don-ramon/cassandra-cli',
    author='don_ramon',
    author_email='alex@rembish.ru',
    install_requires=[
        'pycassa',
        'pyparsing',
        'cmd2',
        'prettytable',
    ]
)
