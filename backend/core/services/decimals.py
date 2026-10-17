"""Authoritative two-decimal normalization. Pure Python: no Django import, no floats."""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_PLAIN = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)$")
_Q = Decimal("0.01")


@dataclass(frozen=True)
class Normalized:
    value: "str | None"   # "5.10" or None
    state: str            # "ok" | "blank" | "invalid"
    rounded: bool         # True if rounding changed the numeric value (e.g. 5.126 -> 5.13)


def normalize(raw, rounding=ROUND_HALF_UP) -> Normalized:
    """None/empty -> blank (null). Anything unparsable -> invalid (never silently 0)."""
    if raw is None:
        return Normalized(None, "blank", False)
    s = str(raw).strip().replace("\u00a0", "").replace(" ", "")
    if s == "":
        return Normalized(None, "blank", False)
    if "," in s and "." not in s and s.count(",") == 1:   # decimal comma
        s = s.replace(",", ".")
    if not _PLAIN.match(s):
        return Normalized(None, "invalid", False)
    try:
        d = Decimal(s)
        q = d.quantize(_Q, rounding=rounding)
    except InvalidOperation:
        return Normalized(None, "invalid", False)
    if q == 0:
        q = abs(q)                                         # never "-0.00"
    return Normalized(format(q, "f"), "ok", q != d)
