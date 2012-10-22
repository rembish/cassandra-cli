from setuptools import setup, find_packages
from ccli import __version__

setup(
    name='cassandra-cli',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cassandra-cli = ccli.cli:main',
        ]
    },
    install_requires=[
        'pycassa',
        'pyparsing',
        'cmd2',
        'prettytable',
    ]
)