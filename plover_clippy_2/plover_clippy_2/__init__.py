"""Plover Windows builds remove the stdlib sqlite3 package.

pysqlite3 is installed with this plugin and stands in for that package.
"""

import sys


def install_sqlite():
    try:
        import sqlite3
    except ModuleNotFoundError:
        import pysqlite3 as sqlite3

        sys.modules["sqlite3"] = sqlite3
    return sqlite3


install_sqlite()
