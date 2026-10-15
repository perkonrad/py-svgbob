"""Points, cells and the small part of parry2d/nalgebra that svgbob uses."""

import math

from .f32 import f32, add, sub, mul, div, sqrt, rround

F32_EPSILON = 1.1920929e-07


class Point(object):
    """A 2D point with f32 coordinates (``crate::Point``).

    Points are ordered by ``y`` first and then ``x``.
    """

    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = f32(x)
        self.y = f32(y)

    def __repr__(self):
        return "Point(%r, %r)" % (self.x, self.y)

    def __str__(self):
        from .f32 import fmt
        return "(%s,%s)" % (fmt(self.x), fmt(self.y))

    def cmp(self, other):
        c = ford(self.y, other.y)
        if c:
            return c
        return ford(self.x, other.x)

    def __eq__(self, other):
        return self.y == other.y and self.x == other.x

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.cmp(other) < 0

    def __le__(self, other):
        return self.cmp(other) <= 0

    def __gt__(self, other):
        return self.cmp(other) > 0

    def __ge__(self, other):
        return self.cmp(other) >= 0

    __hash__ = None

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def scale(self, scale):
        return Point(self.x * scale, self.y * scale)

    def distance(self, other):
        dx = sub(other.x, self.x)
        dy = sub(other.y, self.y)
        return sqrt(add(mul(dx, dx), mul(dy, dy)))

    def align(self):
        x = f32(rround(self.x) + 0.5)
        ry = rround(self.y)
        y = ry + 1.0 if math.fmod(ry, 2.0) % 2.0 == 0.0 else ry
        return Point(x, y)

    def adjust_x(self, units):
        t = mul(f32(units), CellGrid.unit_x())
        return Point(self.x + t, self.y)

    def adjust_y(self, units):
        t = mul(f32(units), CellGrid.unit_y())
        return Point(self.x, self.y + t)

    def adjust(self, units_x, units_y):
        t = mul(f32(units_x), CellGrid.unit_x())
        u = mul(f32(units_y), CellGrid.unit_y())
        return Point(self.x + t, self.y + u)


def ford(f1, f2):
    """``util::ord``: total compare of two floats, panics on NaN."""
    if f1 == f2:
        return 0
    if f1 > f2:
        return 1
    if f1 < f2:
        return -1
    raise ValueError("comparison should only be 3 possibilities: %r %r" % (f1, f2))


def opt_ord(f1, f2):
    if f1 is None and f2 is None:
        return 0
    if f2 is None:
        return 1
    if f1 is None:
        return -1
    return ford(f1, f2)


def bcmp(a, b):
    """Compare two bools / ints the Rust way (false < true)."""
    return (a > b) - (a < b)


def pmin(a, b):
    """``std::cmp::min``: returns ``a`` when equal."""
    return b if b.cmp(a) < 0 else a


def pmax(a, b):
    """``std::cmp::max``: returns ``b`` when equal."""
    return a if b.cmp(a) < 0 else b


class Cell(tuple):
    """A character cell (``Cell``), ordered by ``y`` then ``x``.

    Stored as the tuple ``(y, x)`` so that tuple ordering and hashing match
    the Rust ``Ord`` implementation.
    """

    __slots__ = ()

    def __new__(cls, x, y):
        return tuple.__new__(cls, (y, x))

    @property
    def x(self):
        return self[1]

    @property
    def y(self):
        return self[0]

    def __repr__(self):
        return "Cell(%d, %d)" % (self[1], self[0])

    def __str__(self):
        return "(%d,%d)" % (self[1], self[0])

    def __add__(self, other):
        return Cell(self[1] + other[1], self[0] + other[0])

    def __sub__(self, other):
        return Cell(self[1] - other[1], self[0] - other[0])

    def is_adjacent(self, other):
        return abs(other[1] - self[1]) <= 1 and abs(other[0] - self[0]) <= 1

    def top_left_most(self):
        return Point(self[1] * 1.0, self[0] * 2.0)

    def bottom_right_most(self):
        return Point((self[1] + 1) * 1.0, (self[0] + 1) * 2.0)

    def absolute_position(self, point):
        return Point(self[1] + point.x, self[0] * 2.0 + point.y)

    def localize_point(self, point):
        return Point(point.x - self[1], point.y - self[0] * 2.0)

    def localize_cell(self, cell):
        return Cell(cell[1] - self[1], cell[0] - self[0])

    def is_bounded(self, bound1, bound2):
        lo, hi = Cell.rearrange_bound(bound1, bound2)
        return lo[1] <= self[1] <= hi[1] and lo[0] <= self[0] <= hi[0]

    @staticmethod
    def rearrange_bound(bound1, bound2):
        return (Cell(min(bound1[1], bound2[1]), min(bound1[0], bound2[0])),
                Cell(max(bound1[1], bound2[1]), max(bound1[0], bound2[0])))

    @staticmethod
    def width():
        return 1.0

    @staticmethod
    def height():
        return 2.0

    @staticmethod
    def unit(n):
        return mul(CellGrid.unit_x(), f32(n))

    @staticmethod
    def snap_point(point):
        x = math.floor(point.x / 1.0)
        y = math.floor(div(point.y, 2.0))
        cell = Cell(int(x), int(y))
        return cell, Cell.snap(cell.localize_point(point))

    @staticmethod
    def snap(p):
        tx = div(rround(mul(p.x, 4.0)), 4.0)
        ty = div(rround(mul(p.y, 8.0)), 8.0)
        return Point(tx, ty)

    def top_left(self):
        return Cell(self[1] - 1, self[0] - 1)

    def top(self):
        return Cell(self[1], self[0] - 1)

    def top_right(self):
        return Cell(self[1] + 1, self[0] - 1)

    def left(self):
        return Cell(self[1] - 1, self[0])

    def right(self):
        return Cell(self[1] + 1, self[0])

    def bottom_left(self):
        return Cell(self[1] - 1, self[0] + 1)

    def bottom(self):
        return Cell(self[1], self[0] + 1)

    def bottom_right(self):
        return Cell(self[1] + 1, self[0] + 1)


class CellGrid(object):
    """The 5x9 grid of intersection points inside a cell::

             0 1 2 3 4           B C D
            0┌─┬─┬─┬─┐        A┌─┬─┬─┬─┐E
            1├─┼─┼─┼─┤         │ │ │ │ │
            2├─┼─┼─┼─┤        F├─G─H─I─┤J
            3├─┼─┼─┼─┤         │ │ │ │ │
            4├─┼─┼─┼─┤        K├─L─M─N─┤O
            5├─┼─┼─┼─┤         │ │ │ │ │
            6├─┼─┼─┼─┤        P├─Q─R─S─┤T
            7├─┼─┼─┼─┤         │ │ │ │ │
            8└─┴─┴─┴─┘        U└─┴─┴─┴─┘Y
                                 V W X
    """

    @staticmethod
    def point(x, y):
        return Point(x * 0.25, y * 0.25)

    @staticmethod
    def width():
        return 1.0

    @staticmethod
    def height():
        return 2.0

    @staticmethod
    def unit_x():
        return 0.25

    @staticmethod
    def unit_y():
        return 0.25

    @staticmethod
    def diagonal_length():
        return sqrt(5.0)


_GRID_NAMES = {
    "a": (0, 0), "b": (1, 0), "c": (2, 0), "d": (3, 0), "e": (4, 0),
    "f": (0, 2), "g": (1, 2), "h": (2, 2), "i": (3, 2), "j": (4, 2),
    "k": (0, 4), "l": (1, 4), "m": (2, 4), "n": (3, 4), "o": (4, 4),
    "p": (0, 6), "q": (1, 6), "r": (2, 6), "s": (3, 6), "t": (4, 6),
    "u": (0, 8), "v": (1, 8), "w": (2, 8), "x": (3, 8), "y": (4, 8),
}


def _make_grid_methods():
    for name, (gx, gy) in _GRID_NAMES.items():
        def grid_point(gx=gx, gy=gy):
            return CellGrid.point(gx, gy)

        def cell_point(self, gx=gx, gy=gy):
            return Point(self[1] + gx * 0.25, self[0] * 2.0 + gy * 0.25)

        setattr(CellGrid, name, staticmethod(grid_point))
        # Cell.x / Cell.y are the coordinates, so the grid points named
        # x and y are available as Cell.gx() / Cell.gy()
        setattr(Cell, "g" + name if name in ("x", "y") else name, cell_point)


_make_grid_methods()


def relative_eq(a, b):
    """``approx::relative_eq!`` for f32 with the default epsilons."""
    if a == b:
        return True
    if math.isinf(a) or math.isinf(b):
        return False
    abs_diff = abs(f32(a - b))
    if abs_diff <= F32_EPSILON:
        return True
    largest = max(abs(a), abs(b))
    return abs_diff <= f32(largest * F32_EPSILON)


def segment_contains_point(a, b, pt):
    """parry2d ``Segment::contains_point``.

    The point is projected on the segment and the projection must be
    approximately equal to the point.
    """
    px, py = pt.x, pt.y
    if (px == a.x and py == a.y) or (px == b.x and py == b.y):
        return True
    # The projection lies within the segment's bounding box (give or take
    # an ulp), so a point clearly outside that box can never be within the
    # relative_eq tolerance of it.
    margin = 4.0 * F32_EPSILON * (1.0 + max(abs(px), abs(py), abs(a.x),
                                             abs(a.y), abs(b.x), abs(b.y)))
    if a.x < b.x:
        x0, x1 = a.x, b.x
    else:
        x0, x1 = b.x, a.x
    if px < x0 - margin or px > x1 + margin:
        return False
    if a.y < b.y:
        y0, y1 = a.y, b.y
    else:
        y0, y1 = b.y, a.y
    if py < y0 - margin or py > y1 + margin:
        return False
    abx = sub(b.x, a.x)
    aby = sub(b.y, a.y)
    apx = sub(pt.x, a.x)
    apy = sub(pt.y, a.y)
    ab_ap = add(mul(abx, apx), mul(aby, apy))
    sqnab = add(mul(abx, abx), mul(aby, aby))
    if ab_ap <= 0.0:
        qx, qy = a.x, a.y
    elif ab_ap >= sqnab:
        qx, qy = b.x, b.y
    else:
        u = div(ab_ap, sqnab)
        qx = add(a.x, mul(abx, u))
        qy = add(a.y, mul(aby, u))
    return relative_eq(qx, px) and relative_eq(qy, py)


def is_collinear(a, b, c):
    """True if the triangle a, b, c has an area below 0.01 (Kahan's formula)."""
    la = a.distance(b)
    lb = b.distance(c)
    lc = c.distance(a)
    lc, lb, la = sorted((la, lb, lc))
    sqr = (la + (lb + lc)) * (lc - (la - lb)) * (lc + (la - lb)) * (la + (lb - lc))
    return math.sqrt(max(sqr, 0.0)) * 0.25 < 0.01


def aabb_of(points):
    """Bounding box (mins, maxs) of a list of points."""
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return Point(min(xs), min(ys)), Point(max(xs), max(ys))


def segment_aabb(a, b):
    return (Point(min(a.x, b.x), min(a.y, b.y)),
            Point(max(a.x, b.x), max(a.y, b.y)))
