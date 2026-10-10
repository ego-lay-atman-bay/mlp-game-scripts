from collections.abc import Callable
from datetime import datetime, timezone

def find_first(sequence: list, condition: Callable):
    try:
        return next(value for value in sequence if condition(value))
    except StopIteration:
        return None

def traditional_round(num: float | int, ndigits: int = 0) -> int | float:
    """
    The builtin `round()` method uses "Baker's Rounding", which rounds to the nearest
    even number if the decimal part is at `.5`. For example

    >>> round(1.5) # 2
    >>> round(2.5) # 2
    
    This function instead uses the traditional rounding system, where it will round up instead.
    For example

    >>> traditional_round(1.5) # 2
    >>> traditional_round(2.5) # 3

    Args:
        num (float | int): Input number

    Returns:
        int: Rounded number
    """
    import decimal

    if ndigits < 0:
        num /= 10 ** -ndigits

    rounded = decimal.Decimal(num).quantize(
        decimal.Decimal('1.' + '0' * ndigits),
        rounding=decimal.ROUND_HALF_UP,
    )

    if ndigits < 0:
        rounded *= 10 ** -ndigits

    return float(rounded) if ndigits > 0 else int(rounded)


DATE_FORMAT: str = '%Y-%m-%d %H:%M:%SZ'

def parse_date(date: str, format: str = DATE_FORMAT, tzinfo: timezone = timezone.utc) -> datetime:
    return datetime.strptime(date, format).replace(tzinfo = tzinfo)
