"""Drawing fragments: lines, arcs, circles, polygons, rects and texts.

Fragments are compared with :func:`frag_cmp`, a port of the Rust ``Ord``
implementations.  ``==`` on fragments means ``frag_cmp(...) == 0`` exactly
like the Rust ``PartialEq`` impls.
"""

import math

from . import f32 as F
from .f32 import f32, add, sub, mul, div, sqrt, rround, as_i32
from .geom import (Point, Cell, CellGrid, ford, opt_ord, bcmp, pmin, pmax,
                   segment_contains_point, is_collinear, aabb_of, segment_aabb)
from .svg import Element, Text as TextNode
from .parser import parse_css_tag, ParseError

# Direction
TOP_LEFT, TOP, TOP_RIGHT, LEFT, RIGHT, BOTTOM_LEFT, BOTTOM, BOTTOM_RIGHT = range(8)

_OPPOSITE = {
    TOP_LEFT: BOTTOM_RIGHT, TOP: BOTTOM, TOP_RIGHT: BOTTOM_LEFT,
    LEFT: RIGHT, RIGHT: LEFT, BOTTOM_LEFT: TOP_RIGHT,
    BOTTOM: TOP, BOTTOM_RIGHT: TOP_LEFT,
}


def direction_opposite(d):
    return _OPPOSITE[d]


def threshold_length(d):
    if d in (TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT):
        return CellGrid.diagonal_length()
    if d in (LEFT, RIGHT):
        return CellGrid.width()
    return CellGrid.height()


# Marker
ARROW = "arrow"
CLEAR_ARROW = "clear_arrow"
CIRCLE = "circle"
SQUARE = "square"
DIAMOND = "diamond"
OPEN_CIRCLE = "open_circle"
BIG_OPEN_CIRCLE = "big_open_circle"

# PolygonTag
ARROW_TOP_LEFT = "ArrowTopLeft"
ARROW_TOP = "ArrowTop"
ARROW_TOP_RIGHT = "ArrowTopRight"
ARROW_LEFT = "ArrowLeft"
ARROW_RIGHT = "ArrowRight"
ARROW_BOTTOM_LEFT = "ArrowBottomLeft"
ARROW_BOTTOM = "ArrowBottom"
ARROW_BOTTOM_RIGHT = "ArrowBottomRight"
DIAMOND_BULLET = "DiamondBullet"

_TAG_DIRECTION = {
    ARROW_TOP_LEFT: TOP_LEFT, ARROW_TOP: TOP, ARROW_TOP_RIGHT: TOP_RIGHT,
    ARROW_LEFT: LEFT, ARROW_RIGHT: RIGHT, ARROW_BOTTOM_LEFT: BOTTOM_LEFT,
    ARROW_BOTTOM: BOTTOM, ARROW_BOTTOM_RIGHT: BOTTOM_RIGHT,
    DIAMOND_BULLET: None,
}

_PIS_IN_180 = f32(57.2957795130823208767981548141051703)


def escape_html_text(s):
    out = []
    for ch in s:
        if ch == ">":
            out.append("&gt;")
        elif ch == "<":
            out.append("&lt;")
        elif ch == "&":
            out.append("&amp;")
        elif ch == "'":
            out.append("&#39;")
        elif ch == '"':
            out.append("&quot;")
        elif ch == "\0":
            pass
        else:
            out.append(ch)
    return "".join(out)


def utf8_len(s):
    return len(s.encode("utf-8", "surrogatepass"))


class Fragment(object):
    __slots__ = ("_bnds",)
    rank = 0

    def bounds(self):
        """(mins, maxs) of this fragment, computed once (fragments are immutable)."""
        try:
            return self._bnds
        except AttributeError:
            self._bnds = b = self._compute_bounds()
            return b

    def __eq__(self, other):
        return frag_cmp(self, other) == 0

    def __ne__(self, other):
        return frag_cmp(self, other) != 0

    def __lt__(self, other):
        return frag_cmp(self, other) < 0

    __hash__ = None

    def mins(self):
        return self.bounds()[0]

    def maxs(self):
        return self.bounds()[1]

    def can_fit(self, other):
        tl, br = self.bounds()
        otl, obr = other.bounds()
        return tl.x <= otl.x and tl.y <= otl.y and br.x >= obr.x and br.y >= obr.y

    def line_overlap(self, a, b):
        return False

    def has_endpoint(self, p):
        return False

    def arcs_to(self, a, b):
        return False

    def is_broken(self):
        return False

    def merge(self, other):
        return None

    def is_contacting(self, other):
        return False

    def as_css_tag(self):
        return []

    def is_aabb_parallel(self, other):
        return False

    def to_node(self):
        raise NotImplementedError


class Line(Fragment):
    __slots__ = ("start", "end", "broken")
    rank = 10

    def __init__(self, start, end, is_broken=False, noswap=False):
        if not noswap and start.cmp(end) > 0:
            start, end = end, start
        self.start = start
        self.end = end
        self.broken = is_broken

    def __repr__(self):
        return "L %s %s %s" % (self.start, self.end, self.broken)

    def cmp_same(self, other):
        return (self.start.cmp(other.start) or self.end.cmp(other.end)
                or bcmp(self.broken, other.broken))

    def _compute_bounds(self):
        return segment_aabb(self.start, self.end)

    def is_broken(self):
        return self.broken

    def overlaps(self, a, b):
        return (segment_contains_point(self.start, self.end, a)
                and segment_contains_point(self.start, self.end, b))

    line_overlap = overlaps

    def contains_point(self, p):
        return segment_contains_point(self.start, self.end, p)

    def touching_line(self, other):
        return self.contains_point(other.start) or self.contains_point(other.end)

    def is_touching(self, other):
        # Touching needs an end point of one line on the other line, which
        # needs the bounding boxes to meet (segment_contains_point's
        # tolerance is far below 0.01).
        (a0, a1), (b0, b1) = self.bounds(), other.bounds()
        if (a0.x > b1.x + 0.01 or b0.x > a1.x + 0.01
                or a0.y > b1.y + 0.01 or b0.y > a1.y + 0.01):
            return False
        return self.touching_line(other) or other.touching_line(self)

    def has_endpoint(self, p):
        return self.start == p or self.end == p

    def is_touching_arc(self, other):
        return (self.start == other.start or self.end == other.end
                or self.start == other.end or self.end == other.start)

    def octant(self):
        dx = sub(self.end.x, self.start.x)
        dy = -sub(mul(self.end.y, 2.0), mul(self.start.y, 2.0))
        octant = 0
        if dy < 0.0:
            dx = -dx
            dy = -dy
            octant += 4
        if dx < 0.0:
            tmp = dx
            dx = dy
            dy = -tmp
            octant += 2
        if dx < dy:
            octant += 1
        return octant

    def slope(self):
        return div(sub(mul(2.0, self.end.y), mul(2.0, self.start.y)),
                   sub(self.end.x, self.start.x))

    def angle_deg(self):
        m1 = self.slope()
        rad = f32(0.0 - f32(math.atan(m1))) if m1 == m1 else F.NAN
        return mul(rad, _PIS_IN_180) if rad == rad else F.NAN

    def full_angle(self):
        angle = abs(self.angle_deg())
        o = self.octant()
        if o <= 1:
            return angle
        if o <= 3:
            return sub(180.0, angle)
        if o <= 5:
            return add(180.0, angle)
        if o <= 7:
            return sub(360.0, angle)
        return angle

    def line_angle(self):
        angle = as_i32(rround(self.full_angle()))
        if 0 <= angle <= 10:
            return 0.0
        if 11 <= angle <= 80:
            return 63.435
        if 81 <= angle <= 100:
            return 90.0
        if 101 <= angle <= 170:
            return 116.565
        if 171 <= angle <= 190:
            return 180.0
        if 191 <= angle <= 260:
            return 243.435
        if 261 <= angle <= 280:
            return 270.0
        if 281 <= angle <= 350:
            return 296.565
        return 0.0

    def heading(self):
        a = as_i32(rround(f32(self.line_angle())))
        return {
            0: RIGHT, 45: TOP_RIGHT, 63: TOP_RIGHT, 90: TOP, 117: TOP_LEFT,
            135: TOP_LEFT, 180: LEFT, 225: BOTTOM_LEFT, 243: BOTTOM_LEFT,
            270: BOTTOM, 297: BOTTOM_RIGHT, 315: BOTTOM_RIGHT,
        }[a]

    def is_touching_circle(self, circle):
        center = circle.center
        d_end = self.end.distance(center)
        d_start = self.start.distance(center)
        return d_start < circle.radius or d_end < circle.radius

    def can_merge(self, other):
        return (self.is_touching(other)
                and is_collinear(self.start, self.end, other.start)
                and is_collinear(self.start, self.end, other.end))

    def merge_line(self, other):
        if self.can_merge(other):
            start = pmin(self.start, other.start)
            end = pmax(self.end, other.end)
            return Line(start, end, self.broken or other.broken)
        return None

    def merge_circle(self, circle):
        d_end = self.end.distance(circle.center)
        d_start = self.start.distance(circle.center)
        threshold = threshold_length(self.heading())
        limit = mul(threshold, 0.75)
        close_start = d_start <= limit
        close_end = d_end <= limit
        if circle.radius <= Cell.unit(3) and (close_start or close_end):
            if circle.filled:
                marker = CIRCLE
            elif circle.radius >= Cell.unit(2):
                marker = BIG_OPEN_CIRCLE
            else:
                marker = OPEN_CIRCLE
            if close_end:
                new_line = Line(self.start, circle.center, self.broken, noswap=True)
            else:
                new_line = Line(self.end, circle.center, self.broken, noswap=True)
            return MarkerLine(new_line.start, new_line.end, new_line.broken, None, marker)
        return None

    def merge(self, other):
        if type(other) is Line:
            return self.merge_line(other)
        if type(other) is Circle:
            return self.merge_circle(other)
        return None

    def is_contacting(self, other):
        t = type(other)
        if t is Line:
            return self.is_touching(other)
        if t is Arc:
            return self.is_touching_arc(other)
        if t is Circle:
            return self.is_touching_circle(other)
        return False

    def is_horizontal(self):
        return self.start.y == self.end.y

    def is_vertical(self):
        return self.start.x == self.end.x

    def is_aabb_parallel(self, other):
        if type(other) is not Line:
            return False
        return ((self.is_horizontal() and other.is_horizontal()
                 and self.start.x == other.start.x and self.end.x == other.end.x)
                or (self.is_vertical() and other.is_vertical()
                    and self.start.y == other.start.y and self.end.y == other.end.y))

    def is_aabb_perpendicular(self, other):
        return ((self.is_horizontal() and other.is_vertical())
                or (self.is_vertical() and other.is_horizontal()))

    def is_touching_aabb_perpendicular(self, other):
        return self.is_touching(other) and self.is_aabb_perpendicular(other)

    def absolute_position(self, cell):
        return Line(cell.absolute_position(self.start),
                    cell.absolute_position(self.end), self.broken, noswap=True)

    def scale(self, scale):
        return Line(self.start.scale(scale), self.end.scale(scale), self.broken,
                    noswap=True)

    def extend(self, length):
        d = self.start.distance(self.end)
        cx = add(self.end.x, mul(div(sub(self.end.x, self.start.x), d), length))
        cy = add(self.end.y, mul(div(sub(self.end.y, self.start.y), d), length))
        return Line(self.start, Point(cx, cy), self.broken, noswap=True)

    def extend_start(self, length):
        tmp = Line(self.end, self.start, self.broken, noswap=True).extend(length)
        return Line(tmp.end, tmp.start, tmp.broken, noswap=True)

    def to_node(self):
        return Element("line", [
            ("x1", F.fmt(self.start.x)), ("y1", F.fmt(self.start.y)),
            ("x2", F.fmt(self.end.x)), ("y2", F.fmt(self.end.y)),
            ("class", ["broken" if self.broken else "solid"]),
        ])


class MarkerLine(Fragment):
    __slots__ = ("line", "start_marker", "end_marker")
    rank = 20

    def __init__(self, a, b, is_broken, start_marker, end_marker):
        self.line = Line(a, b, is_broken, noswap=True)
        self.start_marker = start_marker
        self.end_marker = end_marker

    def __repr__(self):
        return "%r %s %s" % (self.line, self.start_marker, self.end_marker)

    def _compute_bounds(self):
        return self.line.bounds()

    def absolute_position(self, cell):
        line = self.line.absolute_position(cell)
        return MarkerLine(line.start, line.end, line.broken,
                          self.start_marker, self.end_marker)

    def scale(self, scale):
        line = self.line.scale(scale)
        return MarkerLine(line.start, line.end, line.broken,
                          self.start_marker, self.end_marker)

    def to_node(self):
        node = self.line.to_node()
        classes = []
        if self.start_marker is not None:
            classes.append(("class", "start_marked_%s" % self.start_marker))
        if self.end_marker is not None:
            classes.append(("class", "end_marked_%s" % self.end_marker))
        return node.with_attributes(classes)


class Circle(Fragment):
    __slots__ = ("center", "radius", "filled")
    rank = 30

    def __init__(self, center, radius, is_filled=False):
        self.center = center
        self.radius = f32(radius)
        self.filled = is_filled

    def __repr__(self):
        return "C %s %s" % (self.center, F.fmt(self.radius))

    def _compute_bounds(self):
        c, r = self.center, self.radius
        return (Point(c.x - r, c.y - r), Point(c.x + r, c.y + r))

    def cmp_same(self, other):
        a0, a1 = self.bounds()
        b0, b1 = other.bounds()
        return (a0.cmp(b0) or a1.cmp(b1) or ford(self.radius, other.radius)
                or bcmp(self.filled, other.filled))

    def merge(self, other):
        if type(other) is Line:
            return other.merge_circle(self)
        return None

    def is_contacting(self, other):
        if type(other) is Line:
            return other.is_touching_circle(self)
        return False

    def absolute_position(self, cell):
        return Circle(cell.absolute_position(self.center), self.radius, self.filled)

    def scale(self, scale):
        return Circle(self.center.scale(scale), mul(self.radius, scale), self.filled)

    def to_node(self):
        return Element("circle", [
            ("cx", F.fmt(self.center.x)), ("cy", F.fmt(self.center.y)),
            ("r", F.fmt(self.radius)),
            ("class", ["filled" if self.filled else "nofill"]),
        ])


class Arc(Fragment):
    __slots__ = ("start", "end", "radius", "major_flag", "sweep_flag",
                 "rotation_flag")
    rank = 40

    def __init__(self, start, end, radius, sweep_flag=False, major_flag=False,
                 rotation_flag=False, reorder=True):
        self.start = start
        self.end = end
        self.radius = f32(radius)
        self.major_flag = major_flag
        self.sweep_flag = sweep_flag
        self.rotation_flag = rotation_flag
        if reorder and start.cmp(end) > 0:
            self.start, self.end = end, start
            self.sweep_flag = not self.sweep_flag

    @staticmethod
    def major(start, end, radius):
        return Arc(start, end, radius, major_flag=True)

    def __repr__(self):
        return "A %s %s %s -> %d %d %d" % (
            self.start, self.end, F.fmt(self.radius), self.rotation_flag,
            self.major_flag, self.sweep_flag)

    def _copy(self, start, end, radius):
        return Arc(start, end, radius, self.sweep_flag, self.major_flag,
                   self.rotation_flag, reorder=False)

    def cmp_same(self, other):
        return (self.start.cmp(other.start) or self.end.cmp(other.end)
                or ford(self.radius, other.radius)
                or bcmp(self.rotation_flag, other.rotation_flag)
                or bcmp(self.major_flag, other.major_flag)
                or bcmp(self.sweep_flag, other.sweep_flag))

    def _compute_bounds(self):
        return segment_aabb(self.start, self.end)

    def arcs_to(self, a, b):
        arc = Arc(a, b, 1.0)
        return (self.start == arc.start and self.end == arc.end
                and self.sweep_flag == arc.sweep_flag)

    def is_touching(self, other):
        return (self.start == other.start or self.end == other.end
                or self.start == other.end or self.end == other.start)

    def has_endpoint(self, p):
        return self.start == p or self.end == p

    def is_contacting(self, other):
        t = type(other)
        if t is Arc:
            return self.is_touching(other)
        if t is Line:
            return other.is_touching_arc(self)
        return False

    def center(self):
        start, end = self.start, self.end
        q = start.distance(end)
        y3 = div(add(start.y, end.y), 2.0)
        x3 = div(add(start.x, end.x), 2.0)
        half_q = div(q, 2.0)
        rr_q22 = sqrt(sub(mul(self.radius, self.radius), mul(half_q, half_q)))
        base_x = div(mul(rr_q22, sub(start.y, end.y)), q)
        base_y = div(mul(rr_q22, sub(end.x, start.x)), q)
        if self.sweep_flag:
            return Point(add(x3, base_x), add(y3, base_y))
        return Point(sub(x3, base_x), sub(y3, base_y))

    def is_aabb_right_angle_arc(self):
        c = self.center()
        return ((c.x == self.start.x and c.y == self.end.y)
                or (c.x == self.end.x and c.y == self.start.y))

    def absolute_position(self, cell):
        return self._copy(cell.absolute_position(self.start),
                          cell.absolute_position(self.end), self.radius)

    def scale(self, scale):
        return self._copy(self.start.scale(scale), self.end.scale(scale),
                          mul(self.radius, scale))

    def to_node(self):
        d = "M %s,%s A %s,%s %d,%d,%d %s,%s" % (
            F.fmt(self.start.x), F.fmt(self.start.y),
            F.fmt(self.radius), F.fmt(self.radius),
            self.rotation_flag, self.major_flag, self.sweep_flag,
            F.fmt(self.end.x), F.fmt(self.end.y))
        return Element("path", [("d", d), ("class", "nofill")])


class Polygon(Fragment):
    __slots__ = ("points", "filled", "tags")
    rank = 50

    def __init__(self, points, is_filled, tags):
        self.points = list(points)
        self.filled = is_filled
        self.tags = list(tags)

    def __repr__(self):
        return "P " + " ".join(str(p) for p in self.points)

    def cmp_same(self, other):
        if len(self.points) == len(other.points) and all(
                a == b for a, b in zip(self.points, other.points)):
            return 0
        return (self.points[0].cmp(other.points[0])
                or self.points[-1].cmp(other.points[-1])
                or bcmp(self.filled, other.filled)
                or bcmp(len(self.points), len(other.points)))

    def _compute_bounds(self):
        return aabb_of(self.points)

    def absolute_position(self, cell):
        return Polygon([cell.absolute_position(p) for p in self.points],
                       self.filled, self.tags)

    def scale(self, scale):
        return Polygon([p.scale(scale) for p in self.points], self.filled, self.tags)

    def to_node(self):
        pts = " ".join("%s,%s" % (F.fmt(p.x), F.fmt(p.y)) for p in self.points)
        return Element("polygon", [
            ("points", pts),
            ("class", ["filled" if self.filled else "nofill"]),
        ])


class Rect(Fragment):
    __slots__ = ("start", "end", "filled", "radius", "broken")
    rank = 60

    def __init__(self, start, end, is_filled, is_broken, radius=None,
                 reorder=True):
        if reorder and start.cmp(end) > 0:
            start, end = end, start
        self.start = start
        self.end = end
        self.filled = is_filled
        self.radius = None if radius is None else f32(radius)
        self.broken = is_broken

    def __repr__(self):
        return "R %s %s" % (self.start, self.end)

    def cmp_same(self, other):
        return (self.start.cmp(other.start) or self.end.cmp(other.end)
                or bcmp(self.filled, other.filled)
                or opt_ord(self.radius, other.radius)
                or bcmp(self.broken, other.broken))

    def _compute_bounds(self):
        return segment_aabb(self.start, self.end)

    def is_broken(self):
        return self.broken

    def absolute_position(self, cell):
        return Rect(cell.absolute_position(self.start),
                    cell.absolute_position(self.end), self.filled, self.broken,
                    self.radius, reorder=False)

    def scale(self, scale):
        return Rect(self.start.scale(scale), self.end.scale(scale), self.filled,
                    self.broken,
                    None if self.radius is None else mul(self.radius, scale),
                    reorder=False)

    def to_node(self):
        classes = ["broken" if self.broken else "solid",
                   "filled" if self.filled else "nofill"]
        return Element("rect", [
            ("x", F.fmt(self.start.x)), ("y", F.fmt(self.start.y)),
            ("width", F.fmt(sub(self.end.x, self.start.x))),
            ("height", F.fmt(sub(self.end.y, self.start.y))),
            ("class", classes),
            ("rx", F.fmt(self.radius) if self.radius is not None else "0"),
        ])


class CellText(Fragment):
    """Text positioned on a cell; ``content`` length is counted in bytes."""
    __slots__ = ("start", "content")
    rank = 80

    def __init__(self, start, content):
        self.start = start
        self.content = content

    def __repr__(self):
        return "CT %s %s" % (self.start, self.content)

    def cmp_same(self, other):
        if self.start != other.start:
            return -1 if self.start < other.start else 1
        if self.content != other.content:
            return -1 if self.content < other.content else 1
        return 0

    def byte_len(self):
        return utf8_len(self.content)

    def end_cell(self):
        return Cell(self.start.x + self.byte_len(), self.start.y)

    def _compute_bounds(self):
        return self.start.top_left_most(), self.end_cell().bottom_right_most()

    def cells(self):
        y = self.start.y
        return [Cell(x, y) for x in range(self.start.x, self.start.x + self.byte_len())]

    def is_adjacent_cell(self, other_cell):
        return any(c.y == other_cell.y and c.is_adjacent(other_cell)
                   for c in self.cells())

    def is_contacting(self, other):
        if type(other) is not CellText:
            return False
        # cells share one row, so only the row and the x ranges matter
        if self.start.y != other.start.y:
            return False
        a0 = self.start.x
        a1 = a0 + self.byte_len()
        b0 = other.start.x
        b1 = b0 + other.byte_len()
        if a1 <= a0 or b1 <= b0:
            return False
        # some x in [a0, a1) and some x' in [b0, b1) with |x - x'| <= 1
        return a0 <= b1 and b0 <= a1

    def can_merge(self, other):
        return (self.start.y == other.start.y
                and (self.start.x + self.byte_len() == other.start.x
                     or other.start.x + other.byte_len() == self.start.x))

    def merge(self, other):
        if type(other) is not CellText or not self.can_merge(other):
            return None
        if self.start.x < other.start.x:
            return CellText(self.start, self.content + other.content)
        return CellText(other.start, other.content + self.content)

    def absolute_position(self, cell):
        return CellText(Cell(self.start.x + cell.x, self.start.y + cell.y),
                        self.content)

    def to_text(self):
        return Text(self.start.q(), self.content)

    def scale(self, scale):
        return self.to_text().scale(scale)

    def as_css_tag(self):
        try:
            return parse_css_tag(self.content)
        except ParseError:
            return []

    def to_node(self):
        return self.to_text().to_node()


class Text(Fragment):
    __slots__ = ("start", "text")
    rank = 70

    def __init__(self, start, text):
        self.start = start
        self.text = text

    def __repr__(self):
        return "T %s %s" % (self.start, self.text)

    def cmp_same(self, other):
        c = self.start.cmp(other.start)
        if c:
            return c
        if self.text != other.text:
            return -1 if self.text < other.text else 1
        return 0

    def _compute_bounds(self):
        width = f32(float(utf8_len(self.text)) * 1.0)
        return self.start, Point(self.start.x + width, self.start.y)

    def absolute_position(self, cell):
        return Text(cell.absolute_position(self.start), self.text)

    def scale(self, scale):
        return Text(self.start.scale(scale), self.text)

    def as_css_tag(self):
        try:
            return parse_css_tag(self.text)
        except ParseError:
            return []

    def to_node(self):
        return Element("text", [("x", F.fmt(self.start.x)),
                                ("y", F.fmt(self.start.y))],
                       [TextNode(escape_html_text(self.text))])


_SAME_TYPE_CMP = (Line, Arc, Circle, Polygon, Rect, Text, CellText)


def frag_cmp(a, b):
    ta = type(a)
    if ta is type(b) and ta in _SAME_TYPE_CMP:
        return a.cmp_same(b)
    a0, a1 = a.bounds()
    b0, b1 = b.bounds()
    return a0.cmp(b0) or a1.cmp(b1) or bcmp(a.rank, b.rank)


def frag_lt(a, b):
    return frag_cmp(a, b) < 0


def rust_sort(items, is_less):
    """Sort in place like Rust's stable ``slice::sort``.

    Slices up to 20 elements use insertion sort, which matters because some
    of the fragment orderings are not transitive across fragment types.
    Longer slices fall back to Python's stable sort.
    """
    n = len(items)
    if n < 2:
        return items
    if n <= 20:
        for i in range(1, n):
            tmp = items[i]
            j = i
            while j > 0 and is_less(tmp, items[j - 1]):
                items[j] = items[j - 1]
                j -= 1
            items[j] = tmp
        return items
    import functools

    def cmp(a, b):
        if is_less(a, b):
            return -1
        if is_less(b, a):
            return 1
        return 0
    items.sort(key=functools.cmp_to_key(cmp))
    return items


def sort_fragments(frags):
    return rust_sort(frags, frag_lt)


def dedup(items):
    """Rust ``Vec::dedup``: drop consecutive duplicates (``==``)."""
    out = []
    for item in items:
        if out and item == out[-1]:
            continue
        out.append(item)
    return out


def polygon_tag_marker(tag):
    return DIAMOND if tag == DIAMOND_BULLET else ARROW


# constructor helpers mirroring the Rust free functions
def line(a, b):
    return Line(a, b, False)


def broken_line(a, b):
    return Line(a, b, True)


def circle(c, r, is_filled):
    return Circle(c, r, is_filled)


def arc(a, b, r):
    return Arc(a, b, r)


def arc_with_sweep(a, b, r, sweep):
    return Arc(a, b, r, sweep_flag=sweep)


def polygon(points, is_filled, tags):
    return Polygon(points, is_filled, tags)


def rect(start, end, is_filled, is_broken):
    return Rect(start, end, is_filled, is_broken)


def rounded_rect(start, end, is_filled, radius, is_broken):
    return Rect(start, end, is_filled, is_broken, radius)


def cell_text(ch):
    return CellText(Cell(0, 0), ch)
