"""Emulation of Rust ``f32`` arithmetic and formatting.

svgbob computes all geometry in single precision and some decisions depend
on exact float equality (e.g. whether an arc's center is axis-aligned with
its end points).  Python floats are doubles, so every arithmetic result that
the Rust code stores in an ``f32`` is rounded here with :func:`f32`.

For ``+ - * /`` and ``sqrt`` on f32 inputs, computing in double precision and
rounding once to single precision gives exactly the IEEE single precision
result, so ``f32(a + b)`` matches Rust's ``a + b``.
"""

import math
import struct

_F = struct.Struct("<f")
_pack = _F.pack
_unpack = _F.unpack

INF = float("inf")
NAN = float("nan")


_cache = {}


def f32(x):
    """Round a Python float to the nearest IEEE single precision value."""
    r = _cache.get(x)
    if r is not None and x != 0.0:  # 0.0 == -0.0, keep the sign of zero
        return r
    try:
        r = _unpack(_pack(x))[0]
    except OverflowError:
        r = INF if x > 0 else -INF
    if len(_cache) < 100000:
        _cache[x] = r
    return r


def add(a, b):
    return f32(a + b)


def sub(a, b):
    return f32(a - b)


def mul(a, b):
    return f32(a * b)


def div(a, b):
    """IEEE division (Rust never raises on division by zero)."""
    if b == 0.0:
        if a != a or a == 0.0:
            return NAN
        neg = (a < 0) != (math.copysign(1.0, b) < 0)
        return -INF if neg else INF
    return f32(a / b)


def sqrt(a):
    if a != a or a < 0:
        return NAN
    return f32(math.sqrt(a))


def rround(x):
    """Rust ``f32::round``: round half away from zero."""
    if x != x or x in (INF, -INF):
        return x
    if x >= 0:
        r = math.floor(x + 0.5)
        # guard against x + 0.5 rounding up for values just below .5
        if r - x > 0.5:
            r -= 1
    else:
        r = -math.floor(-x + 0.5)
        if x - r > 0.5:
            r += 1
    return float(r)


def as_i32(x):
    """Rust ``x as i32``: saturating cast, NaN becomes 0."""
    if x != x:
        return 0
    if x >= 2147483647:
        return 2147483647
    if x <= -2147483648:
        return -2147483648
    return int(x)  # truncates toward zero


def fract(x):
    """Rust ``f32::fract``: ``x - x.trunc()``."""
    return f32(x - math.trunc(x))


def _shortest_digits(v):
    """Shortest decimal digits that round-trip to the f32 ``v``.

    Returns (digits, exponent) such that v ~= 0.d1d2d3... * 10**exponent.
    """
    best = None
    for prec in range(1, 10):
        s = "%.*e" % (prec - 1, v)
        mant, exp = s.split("e")
        digits = mant.replace(".", "")
        exp = int(exp)
        base = int(digits)
        candidates = []
        for d in (base - 1, base, base + 1):
            if d <= 0:
                continue
            ds = str(d)
            e = exp
            if len(ds) > prec:  # carried, e.g. 99 + 1 = 100
                ds = ds[:prec]
                e += 1
            elif len(ds) < prec:
                continue
            val = float("%se%d" % (ds[0] + "." + ds[1:] if len(ds) > 1 else ds, e))
            if f32(val) == v:
                # on a tie Rust rounds the last digit up
                candidates.append((abs(val - v), -d, ds, e))
        if candidates:
            candidates.sort()
            _, _, ds, e = candidates[0]
            best = (ds.rstrip("0") or "0", e + 1)
            break
    if best is None:
        s = repr(v)
        raise ValueError("cannot format f32 %s" % s)
    return best


def fmt(x):
    """Format a number the way Rust's ``Display`` formats an ``f32``.

    Integers print without a fractional part (``8``), other values print
    the shortest representation that round-trips (``502.8``), never in
    exponent notation.
    """
    v = f32(x)
    if v != v:
        return "NaN"
    if v == INF:
        return "inf"
    if v == -INF:
        return "-inf"
    sign = "-" if math.copysign(1.0, v) < 0 else ""
    v = abs(v)
    if v == 0.0:
        return sign + "0"
    digits, exp = _shortest_digits(v)
    # value = 0.digits * 10**exp
    n = len(digits)
    if exp <= 0:
        s = "0." + "0" * (-exp) + digits
    elif exp >= n:
        s = digits + "0" * (exp - n)
    else:
        s = digits[:exp] + "." + digits[exp:]
    return sign + s
