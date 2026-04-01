from enum import IntEnum

from .schema import Field, Schema


class Exchange(IntEnum):
    """
    Enum class for stock exchanges.
    """

    SZ = 1  # Shenzhen Stock Exchange
    SH = 2  # Shanghai Stock Exchange
    BJ = 3  # Beijing Stock Exchange

    @staticmethod
    def from_str(s: str) -> "Exchange":
        match s.upper():
            case "SZ":
                return Exchange.SZ
            case "SH":
                return Exchange.SH
            case "BJ":
                return Exchange.BJ
            case _:
                raise ValueError(f"Unknown exchange code: {s}")

    def __str__(self) -> str:
        match self:
            case Exchange.SZ:
                return "SZ"
            case Exchange.SH:
                return "SH"
            case Exchange.BJ:
                return "BJ"


class Symbol:
    """
    Class representing an instrument symbol.
    """

    __slots__ = ["exchange", "number"]

    def __init__(self, exchange: Exchange, number: int):
        self.exchange = exchange
        self.number = number

    @staticmethod
    def from_str(s: str) -> "Symbol":
        if s[6] != ".":
            raise ValueError(f"Invalid symbol format: {s}")
        exchange, number = Exchange.from_str(s[7:]), int(s[:6])
        return Symbol(exchange, number)

    @staticmethod
    def from_stock_str(s: str) -> "Symbol":
        if len(s) != 6 or not s.isdigit():
            raise ValueError(f"Invalid stock symbol format: {s}")
        number = int(s)
        if number < 600000:
            exchange = Exchange.SZ
        elif number < 800000:
            exchange = Exchange.SH
        else:
            exchange = Exchange.BJ
        return Symbol(exchange, number)

    def __str__(self) -> str:
        return f"{self.number:06}.{self.exchange}"


class ReportKind(IntEnum):
    """
    Enum class for financial report kinds.
    """

    FINANCIAL_INDICATORS = 1
    BALANCE_SHEET = 2
    INCOME_STATEMENT = 3
    CASH_FLOW_STATEMENT = 4


class ReportFormat(IntEnum):
    """
    Enum class for financial report formats.
    """

    GENERAL = 1
    BANK = 2
    SECURITIES = 3
    INSURANCE = 4
