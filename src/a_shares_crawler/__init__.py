"""Data crawler module.

This module provides functions that download and cache financial data from various internet sources.
Currently focused on EastMoney for A-shares stock market data. Some functions are adapted from
AKShare.
"""

__version__ = "0.1.0"

from .types import Exchange, Symbol, ReportKind, ReportFormat, Field, Schema
from .session import load_config, create_session
