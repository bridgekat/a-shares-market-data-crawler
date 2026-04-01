"""Data crawler module.

This module provides functions that download and cache financial data from various internet sources.
Currently focused on EastMoney for A-shares stock market data. Some functions are adapted from
AKShare.
"""

from . import types
from . import session
from . import fetch
from . import parse
from . import download
from . import utils


__all__ = [
    "types",
    "session",
    "fetch",
    "parse",
    "download",
    "utils",
]
