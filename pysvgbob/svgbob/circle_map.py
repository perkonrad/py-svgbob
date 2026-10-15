"""Circle and arc templates (``map/circle_map.rs``).

When a span of characters contains one of these ascii art circles (or a
quarter, half or three quarters of one) it is endorsed as a circle or arc.
"""

import math

from .f32 import f32, add, sub, mul, div
from .geom import Cell, Point
from .fragment import Arc, Circle

# skip the first 3 circles for constructing our arcs, otherwise it will just be a mess
CIRCLES_TO_SKIP_FOR_ARC = 3

# Horizontal edge case of the circle art
LEFT_EDGE = "LeftEdge"  # the left most cell touches the left edge, e.g. `/`
HALF = "Half"  # the left most cell starts at half the cell, e.g. `(` or `|`

# (art, edge case, cells from the left to center.x, cells from the top to center.y)
CIRCLE_ART_MAP = [
    # CIRCLE_0
    (r"""
()
""", HALF, 1.0, 0.5),
    # CIRCLE_1
    (r"""
(_)
""", HALF, 1.5, 0.5),
    # CIRCLE_2
    (r"""
 __
(__)
""", HALF, 2.0, 1.5),
    # CIRCLE_3
    (r"""
 ,-.
(   )
 `-'
""", HALF, 2.5, 1.5),
    # CIRCLE_4
    (r"""
 .--.
(    )
 `--'
""", HALF, 3.0, 1.5),
    # CIRCLE_5
    (r"""
   _
 .' '.
(     )
 `._.'
""", HALF, 3.5, 2.5),
    # CIRCLE_6
    (r"""
   __
 ,'  '.
(      )
 `.__.'
""", HALF, 4.0, 2.5),
    # CIRCLE_7
    (r"""
   ___
 ,'   '.
(       )
 `.   .'
   `-'
""", HALF, 4.5, 2.5),
    # CIRCLE_8
    (r"""
   ___
 ,'   `.
/       \
\       /
 `.___.'
""", LEFT_EDGE, 4.5, 3.0),
    # CIRCLE_9
    (r"""
   ____
 ,'    `.
/        \
\        /
 `.____.'
""", LEFT_EDGE, 5.0, 3.0),
    # CIRCLE_10
    (r"""
    ____
  .'    `.
 /        \
(          )
 \        /
  `.____.'
""", HALF, 6.0, 3.5),
    # CIRCLE_11
    (r"""
    _____
  ,'     `.
 /         \
(           )
 \         /
  `._____.'
""", HALF, 6.5, 3.5),
    # CIRCLE_12
    (r"""
    ______
  ,'      `.
 /          \
|            |
|            |
 \          /
  `.______.'
""", HALF, 7.0, 4.0),
    # CIRCLE_13
    (r"""
    _______
  ,'       `.
 /           \
|             |
|             |
 \           /
  `._______.'
""", HALF, 7.5, 4.0),
    # CIRCLE_14
    (r"""
    ________
  ,'        `.
 /            \
|              |
|              |
|              |
 \            /
  `.________.'
""", HALF, 8.0, 4.5),
    # CIRCLE_15
    (r"""
    __-----__
  ,'         `.
 /             \
|               |
|               |
|               |
 \             /
  `.         .'
    `-------'
""", HALF, 8.5, 4.5),
    # CIRCLE_16
    (r"""
    .--------.
  ,'          `.
 /              \
|                |
|                |
|                |
 \              /
  `.          .'
    `--------'
""", HALF, 9.0, 4.5),
    # CIRCLE_17
    (r"""
    _.-'''''-._
  ,'           `.
 /               \
.                 .
|                 |
|                 |
|                 |
 \               /
  `._         _.'
     '-.....-'
""", HALF, 9.5, 5.5),
    # CIRCLE_18
    (r"""
    _.-''''''-._
  ,'            `.
 /                \
.                  .
|                  |
|                  |
|                  |
 \                /
  `._          _.'
     '-......-'
""", HALF, 10.0, 5.5),
    # CIRCLE_19
    (r"""
    _.-'''''''-._
  ,'             `.
 /                 \
.                   .
|                   |
|                   |
|                   |
 \                 /
  `._           _.'
     '-.......-'
""", HALF, 10.5, 5.5),
    # CIRCLE_20
    (r"""
    _.-''''''''-._
  ,'              `.
 /                  \
.                    .
|                    |
|                    |
|                    |
|                    |
 \                  /
  `._            _.'
     '-........-'
""", HALF, 11.0, 5.5),
    # CIRCLE_21
    (r"""
    _.-'''''''''-._
  ,'               `.
 /                   \
.                     .
|                     |
|                     |
|                     |
|                     |
 \                   /
  `._             _.'
     '-.........-'
""", HALF, 11.5, 5.5),
]


class CircleArt(object):
    def __init__(self, ascii_art, start_edge, offset_center_x, offset_center_y):
        self.ascii_art = ascii_art
        self.start_edge = start_edge
        self.offset_center_x = f32(offset_center_x)
        self.offset_center_y = f32(offset_center_y)

    def edge_increment_x(self):
        return 0.0 if self.start_edge == LEFT_EDGE else 0.5

    def is_shared_x(self):
        return math.fmod(mul(self.offset_center_x, 2.0), 2.0) == 1.0

    def is_shared_y(self):
        return math.fmod(mul(self.offset_center_y, 2.0), 2.0) == 1.0

    def center_cell(self):
        cx = sub(self.offset_center_x, self.edge_increment_x())
        if not self.is_shared_x():
            cx = sub(cx, 0.5)
        cy = self.offset_center_y
        if not self.is_shared_y():
            cy = sub(cy, 0.5)
        return Cell(int(math.floor(cx)), int(math.floor(cy)))

    def width(self):
        from .buffer import CellBuffer
        lo, hi = CellBuffer.from_str(self.ascii_art).bounds()
        if self.start_edge == LEFT_EDGE:
            return f32(float(hi.x - lo.x) + 1.0)
        return f32(float(hi.x - lo.x))

    def radius(self):
        return div(self.width(), 2.0)

    def diameter(self):
        return int(math.floor(mul(self.radius(), 2.0)))

    def center(self):
        return Point(add(self.radius(), self.edge_increment_x()),
                     mul(self.offset_center_y, 2.0))


def circle_art_to_span(art):
    from .buffer import CellBuffer
    spans = CellBuffer.from_str(art).spans()
    assert len(spans) == 1
    return spans[0].localize()


def _quadrant_parameters(circle_art, span):
    """Bounds of the span plus the centers used to cut it into quadrants."""
    tl, br = span.bounds()
    top_left = tl
    bottom_right = br
    top_right = Cell(br.x, tl.y)
    bottom_left = Cell(tl.x, br.y)

    center = circle_art.center()
    radius = circle_art.radius()

    p1 = Point(add(center.x, radius), center.y)
    p2 = Point(center.x, sub(center.y, radius))
    p3 = Point(sub(center.x, radius), center.y)
    p4 = Point(center.x, add(center.y, radius))

    arc2_center = circle_art.center_cell()
    cx = int(math.floor(center.x) / 1.0)
    cy = int(math.floor(center.y) / 2.0)
    span1_center = Cell(cx, arc2_center.y)
    span2_center = arc2_center
    span3_center = Cell(arc2_center.x, cy)
    span4_center = Cell(cx, cy)
    return dict(top_left=top_left, bottom_right=bottom_right,
                top_right=top_right, bottom_left=bottom_left, radius=radius,
                p1=p1, p2=p2, p3=p3, p4=p4,
                span1_center=span1_center, span2_center=span2_center,
                span3_center=span3_center, span4_center=span4_center)


def _quarter_bounds(q):
    return (Cell.rearrange_bound(q["span1_center"], q["top_right"]),
            Cell.rearrange_bound(q["top_left"], q["span2_center"]),
            Cell.rearrange_bound(q["bottom_left"], q["span3_center"]),
            Cell.rearrange_bound(q["span4_center"], q["bottom_right"]))


def _quarter_arcs(circle_art):
    span = circle_art_to_span(circle_art.ascii_art)
    q = _quadrant_parameters(circle_art, span)
    b1, b2, b3, b4 = _quarter_bounds(q)
    radius = q["radius"]
    p1, p2, p3, p4 = q["p1"], q["p2"], q["p3"], q["p4"]
    return [
        (Arc(b1[0].localize_point(p1), b1[0].localize_point(p2), radius),
         span.extract(b1[0], b1[1]).localize()),
        (Arc(b2[0].localize_point(p2), b2[0].localize_point(p3), radius),
         span.extract(b2[0], b2[1]).localize()),
        (Arc(b3[0].localize_point(p3), b3[0].localize_point(p4), radius),
         span.extract(b3[0], b3[1]).localize()),
        (Arc(b4[0].localize_point(p4), b4[0].localize_point(p1), radius),
         span.extract(b4[0], b4[1]).localize()),
    ]


def _half_arcs(circle_art):
    span = circle_art_to_span(circle_art.ascii_art)
    q = _quadrant_parameters(circle_art, span)
    radius = q["radius"]
    p1, p2, p3, p4 = q["p1"], q["p2"], q["p3"], q["p4"]
    top_left, bottom_right = q["top_left"], q["bottom_right"]
    top_right, bottom_left = q["top_right"], q["bottom_left"]

    top_tangent = Cell(top_right.x, q["span1_center"].y)
    bottom_tangent = Cell(bottom_left.x, q["span3_center"].y)
    left_tangent = Cell(q["span2_center"].x, top_left.y)
    right_tangent = Cell(q["span1_center"].x, top_right.y)

    bounds_top = Cell.rearrange_bound(top_left, top_tangent)
    bounds_bottom = Cell.rearrange_bound(bottom_tangent, bottom_right)
    bounds_left = Cell.rearrange_bound(left_tangent, bottom_left)
    bounds_right = Cell.rearrange_bound(right_tangent, bottom_right)

    return [
        (Arc(p1, p3, radius),
         span.extract(bounds_top[0], bounds_top[1]).localize()),
        (Arc(bounds_bottom[0].localize_point(p3),
             bounds_bottom[0].localize_point(p1), radius),
         span.extract(bounds_bottom[0], bounds_bottom[1]).localize()),
        (Arc(p2, p4, radius),
         span.extract(bounds_left[0], bounds_left[1]).localize()),
        (Arc(bounds_right[0].localize_point(p4),
             bounds_right[0].localize_point(p2), radius),
         span.extract(bounds_right[0], bounds_right[1]).localize()),
    ]


def _three_quarters_arcs(circle_art):
    span = circle_art_to_span(circle_art.ascii_art)
    q = _quadrant_parameters(circle_art, span)
    b1, b2, b3, b4 = _quarter_bounds(q)
    radius = q["radius"]
    p1, p2, p3, p4 = q["p1"], q["p2"], q["p3"], q["p4"]
    span1 = span.extract(b1[0], b1[1])
    span2 = span.extract(b2[0], b2[1])
    span3 = span.extract(b3[0], b3[1])
    span4 = span.extract(b4[0], b4[1])
    return [
        (Arc.major(p1, p4, radius),
         span1.merge_no_check(span2).merge_no_check(span3).localize()),
        (Arc.major(p2, p1, radius),
         span2.merge_no_check(span3).merge_no_check(span4).localize()),
        (Arc.major(p3, p2, radius),
         span3.merge_no_check(span4).merge_no_check(span1).localize()),
        (Arc.major(p4, p3, radius),
         span4.merge_no_check(span1).merge_no_check(span2).localize()),
    ]


def _flatten(builder):
    """BTreeMap<diameter, arcs> flattened into [(arc, span)] sorted by
    (diameter, arc index); a later circle art with the same diameter wins."""
    by_diameter = {}
    for circle_art in CIRCLE_MAP[CIRCLES_TO_SKIP_FOR_ARC:]:
        by_diameter[circle_art.diameter()] = builder(circle_art)
    out = []
    for diameter in sorted(by_diameter):
        out.extend(by_diameter[diameter])
    return out


def _build_circles_span():
    """IndexMap<Circle, Span>, kept in insertion order."""
    out = []
    for circle_art in CIRCLE_MAP:
        circle = Circle(circle_art.center(), circle_art.radius(), False)
        span = circle_art_to_span(circle_art.ascii_art)
        for idx, (existing, _) in enumerate(out):
            if existing == circle:
                out[idx] = (existing, span)
                break
        else:
            out.append((circle, span))
    return out


CIRCLE_MAP = [CircleArt(*entry) for entry in CIRCLE_ART_MAP]
CIRCLES_SPAN = _build_circles_span()
FLATTENED_QUARTER_ARC_SPAN = _flatten(_quarter_arcs)
FLATTENED_HALF_ARC_SPAN = _flatten(_half_arcs)
FLATTENED_THREE_QUARTERS_ARC_SPAN = _flatten(_three_quarters_arcs)

# the (cell, char) sets of the templates, for fast subset tests
_CIRCLES = [(frag, span, frozenset(span.items)) for frag, span in CIRCLES_SPAN]
_QUARTERS = [(frag, span, frozenset(span.items))
             for frag, span in FLATTENED_QUARTER_ARC_SPAN]
_HALVES = [(frag, span, frozenset(span.items))
           for frag, span in FLATTENED_HALF_ARC_SPAN]
_THREE_QUARTERS = [(frag, span, frozenset(span.items))
                   for frag, span in FLATTENED_THREE_QUARTERS_ARC_SPAN]


def _endorse(templates, search):
    """Find the last template whose cells are all in ``search`` (localized).

    Returns (fragment, span of the unmatched cells of ``search``) or None.
    """
    from .buffer import Span
    localized = search.localize().items
    big_set = frozenset(localized)
    for frag, span, template_set in reversed(templates):
        if template_set <= big_set:
            unmatched = [search.items[i] for i, item in enumerate(localized)
                         if item not in template_set]
            return frag, Span(unmatched)
    return None


def endorse_circle_span(search):
    return _endorse(_CIRCLES, search)


def endorse_quarter_arc_span(search):
    return _endorse(_QUARTERS, search)


def endorse_half_arc_span(search):
    return _endorse(_HALVES, search)


def endorse_three_quarters_arc_span(search):
    return _endorse(_THREE_QUARTERS, search)
