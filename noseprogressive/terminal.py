from collections import defaultdict
from curses import tigetstr, setupterm, tparm
import os
from os import isatty
import sys


__all__ = ['Terminal']


class Terminal(object):
    """An abstraction around terminal capabilities

    Unlike curses, this doesn't require clearing the screen before doing
    anything.

    """
    def __init__(self, kind=None, stream=None):
        """Initialize the terminal.

        :arg kind: A terminal string as taken by setupterm(). Defaults to the
            value of the TERM environment variable.
        :arg stream: A file-like object representing the terminal. Defaults to
            the original value of stdout, like ``curses.initscr()`` does.

        If ``stream`` is not a tty, I will default to returning '' for all
        capability values, so things like piping your output to a file will
        work nicely.

        """
        if stream is None:
            stream = sys.__stdout__
        if hasattr(stream, 'fileno') and isatty(stream.fileno()):
            # Make things like tigetstr() work:
            # (Explicit args make setupterm() work even when -s is passed.)
            setupterm(kind or os.environ.get('TERM', 'unknown'),
                      stream.fileno())
            # Cache capability codes, because IIRC tigetstr requires a
            # conversation with the terminal.
            self._codes = {}
        else:
            self._codes = NullDict(lambda: '')

    def __getattr__(self, attr):
        """Return parametrized terminal capabilities, like bold.

        For example, you can say ``some_term.bold`` to get the string that
        turns on bold formatting and ``some_term.sgr0`` to get the string that
        turns it off again. For a parametrized capability like ``cup``, pass
        the parameter too: ``some_term.cup(line, column)``.

        ``man terminfo`` for a complete list of capabilities.

        """
        if attr not in self._codes:
            self._codes[attr] = tigetstr(attr)
        return CallableString(self._codes[attr])

    # Sugary names for commonly-used capabilities, intended to help avoid trips
    # to the terminfo man page:

    @property
    def save(self):
        return self.sc

    @property
    def restore(self):
        return self.rc

    @property
    def normal(self):
        return self.sgr0

    @property
    def clear_eol(self):
        return self.el

    @property
    def position(self):
        return self.cup


class CallableString(str):
    """A string which can be called to parametrize it as a terminal capability"""
    def __call__(self, *args):
        return tparm(self, *args)


class NullDict(defaultdict):
    """A ``defaultdict`` that pretends to contain all keys"""
    def __contains__(self, key):
        return True