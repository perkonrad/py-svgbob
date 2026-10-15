"""Behavior of the ascii characters (``map/ascii_map.rs``).

Each entry lists the signature fragments of a character with their signal
strength, and a behavior function that returns (condition, fragments)
pairs given the 8 surrounding properties::

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

from .f32 import mul
from .geom import Cell, CellGrid
from .fragment import (arc, broken_line, circle, line, polygon, rect,
                       ARROW_BOTTOM, ARROW_BOTTOM_LEFT, ARROW_BOTTOM_RIGHT,
                       ARROW_LEFT, ARROW_RIGHT, ARROW_TOP, ARROW_TOP_LEFT,
                       ARROW_TOP_RIGHT, DIAMOND_BULLET)
from .property import Property, STRONG, MEDIUM, WEAK


def _build():
    cell = Cell(0, 0)
    G = CellGrid
    a, b, c, d, e = G.a(), G.b(), G.c(), G.d(), G.e()
    f, g, h, i, j = G.f(), G.g(), G.h(), G.i(), G.j()
    k, l, m, n, o = G.k(), G.l(), G.m(), G.n(), G.o()
    p, q, r, s, t = G.p(), G.q(), G.r(), G.s(), G.t()
    u, v, w, x, y = G.u(), G.v(), G.w(), G.x(), G.y()

    _03 = G.point(0, 3)
    _43 = G.point(4, 3)
    _05 = G.point(0, 5)
    _45 = G.point(4, 5)

    unit1 = Cell.unit(1)  # 0.25
    unit1_5 = mul(Cell.unit(1), 1.5)  # 0.375
    unit2 = Cell.unit(2)  # 0.5
    unit4 = Cell.unit(4)  # 1.0
    unit6 = Cell.unit(6)  # 1.5
    unit8 = Cell.unit(8)  # 2.0
    between1_2 = (unit1 + unit2) / 2.0  # 0.375

    table = []

    def entry(ch, signature):
        def deco(fn):
            table.append((ch, signature, fn))
            return fn
        return deco

    # dash -
    @entry("-", [(STRONG, [line(k, o)])])
    def _dash(top_left, top, top_right, left, right, bottom_left, bottom,
              bottom_right):
        return [(True, [line(k, o)])]

    # tilde ~
    @entry("~", [(STRONG, [broken_line(k, o)])])
    def _tilde(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [(True, [broken_line(k, o)])]

    # vertical line |
    @entry("|", [(STRONG, [line(c, w)])])
    def _vertical(top_left, top, top_right, left, right, bottom_left, bottom,
                  bottom_right):
        return [
            (not bottom_left.is_("/") and not bottom_right.is_("\\")
             and not top_left.is_("\\") and not top_right.is_("/"),
             [line(c, w)]),
            #   _
            #  |
            (top_right.line_overlap(u, v), [line(c, e)]),
            # _
            #  |
            (top_left.line_overlap(x, y), [line(a, c)]),
            #  |_
            (right.line_overlap(u, v), [line(w, y)]),
            #  _|
            (left.line_overlap(x, y), [line(u, w)]),
            #  |-
            (right.line_strongly_overlap(k, l), [line(m, o)]),
            #  -|
            (left.line_strongly_overlap(n, o), [line(k, m)]),
            #    |
            #   /
            (bottom_left.line_overlap(e, u), [line(c, m), line(m, u)]),
            #   |
            #    \
            (bottom_right.line_overlap(a, y), [line(c, m), line(m, y)]),
            #    \ /
            #     |
            (top_left.line_overlap(a, y) and top_right.line_overlap(e, u),
             [line(a, m), line(m, w), line(m, e)]),
        ]

    # exclamation bang !
    @entry("!", [(STRONG, [broken_line(c, w)])])
    def _bang(top_left, top, top_right, left, right, bottom_left, bottom,
              bottom_right):
        return [(top.line_strongly_overlap(r, w)
                 or bottom.line_strongly_overlap(c, h),
                 [broken_line(c, w)])]

    # colon :
    @entry(":", [(STRONG, [broken_line(c, w)])])
    def _colon(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [(top.line_strongly_overlap(r, w)
                 or bottom.line_strongly_overlap(c, h),
                 [broken_line(c, w)])]

    # plus cross +
    @entry("+", [(MEDIUM, [line(c, w), line(k, o)]),
                 (WEAK, [line(a, y), line(u, e)])])
    def _plus(top_left, top, top_right, left, right, bottom_left, bottom,
              bottom_right):
        return [
            (top.line_overlap(r, w), [line(c, m)]),
            (bottom.line_overlap(c, h), [line(m, w)]),
            (left.line_overlap(n, o), [line(k, m)]),
            (right.line_overlap(k, l), [line(m, o)]),
            (left.line_weakly_overlap(n, o), [line(k, m)]),
            (right.line_weakly_overlap(k, l), [line(m, o)]),
            (top_left.line_overlap(s, y), [line(a, m)]),
            (bottom_right.line_overlap(a, g), [line(m, y)]),
            (top_right.line_overlap(q, u), [line(m, e)]),
            (bottom_left.line_overlap(e, i), [line(m, u)]),
        ]

    # letter X
    @entry("X", [(STRONG, [line(a, y), line(u, e)])])
    def _big_x(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [
            (left.line_strongly_overlap(m, o), [line(m, k)]),
            (right.line_strongly_overlap(k, l), [line(m, o)]),
            (top.line_strongly_overlap(r, w), [line(m, c)]),
            (bottom.line_strongly_overlap(c, h), [line(m, w)]),
            (top_left.line_strongly_overlap(s, y), [line(m, a)]),
            (top_right.line_strongly_overlap(u, q), [line(m, e)]),
            (bottom_left.line_strongly_overlap(e, i), [line(m, u)]),
            (bottom_right.line_strongly_overlap(a, g), [line(m, y)]),
        ]

    def _any_strong_connection(top_left, top, top_right, left, right,
                               bottom_left, bottom, bottom_right):
        return (top.line_strongly_overlap(r, w)
                or bottom.line_strongly_overlap(c, h)
                or left.line_strongly_overlap(n, o)
                or right.line_strongly_overlap(k, l)
                or top_left.line_strongly_overlap(s, y)
                or bottom_right.line_strongly_overlap(a, g)
                or bottom_left.line_strongly_overlap(u, q)
                or top_right.line_strongly_overlap(e, i))

    # asterisk *
    @entry("*", [(STRONG, [circle(m, unit1_5, True)]),
                 (MEDIUM, [line(c, w), line(k, o)]),
                 (WEAK, [line(a, y), line(u, e)])])
    def _asterisk(top_left, top, top_right, left, right, bottom_left, bottom,
                  bottom_right):
        return [
            (_any_strong_connection(top_left, top, top_right, left, right,
                                    bottom_left, bottom, bottom_right),
             [circle(m, unit1_5, True)]),
            (top.line_strongly_overlap(r, w), [line(c, h)]),
            (bottom.line_strongly_overlap(c, h), [line(w, r)]),
            (left.line_overlap(n, o), [line(k, m)]),
            (right.line_overlap(k, l), [line(m, o)]),
            (top_left.line_strongly_overlap(s, y), [line(a, g)]),
            (top_right.line_strongly_overlap(u, q), [line(e, i)]),
            (bottom_left.line_strongly_overlap(e, i), [line(u, q)]),
            (bottom_right.line_strongly_overlap(a, g), [line(s, y)]),
        ]

    # hash pound #
    @entry("#", [(STRONG, [rect(f, t, True, False)]),
                 (MEDIUM, [line(c, w), line(k, o)]),
                 (WEAK, [line(a, y), line(u, e)])])
    def _hash(top_left, top, top_right, left, right, bottom_left, bottom,
              bottom_right):
        return [
            (top.line_overlap(r, w) or bottom.line_overlap(c, h)
             or left.line_overlap(n, o) or right.line_overlap(k, l),
             [rect(f, t, True, False)]),
            (top_left.line_overlap(s, y) or bottom_right.line_overlap(a, g)
             or bottom_left.line_overlap(u, q) or top_right.line_overlap(e, i),
             [polygon([m.adjust(1.4, 2.0), m.adjust(1.4, -2.0),
                       m.adjust(-1.4, -2.0), m.adjust(-1.4, 2.0)],
                      True, [DIAMOND_BULLET])]),
            (top.line_overlap(r, w), [line(c, h)]),
            (bottom.line_overlap(c, h), [line(r, w)]),
            (top_left.line_strongly_overlap(s, y), [line(a, g)]),
            (top_right.line_strongly_overlap(u, q), [line(e, i)]),
            (bottom_left.line_strongly_overlap(e, i), [line(u, q)]),
            (bottom_right.line_strongly_overlap(a, g), [line(s, y)]),
        ]

    def _round_bullet(radius):
        def behavior(top_left, top, top_right, left, right, bottom_left,
                     bottom, bottom_right):
            return [
                (_any_strong_connection(top_left, top, top_right, left, right,
                                        bottom_left, bottom, bottom_right),
                 [circle(m, radius, False)]),
                (top.line_strongly_overlap(r, w), [line(c, h)]),
                (bottom.line_strongly_overlap(c, h), [line(w, r)]),
                (top_left.line_strongly_overlap(s, y), [line(a, g)]),
                (top_right.line_strongly_overlap(u, q), [line(e, i)]),
                (bottom_left.line_strongly_overlap(e, i), [line(u, q)]),
                (bottom_right.line_strongly_overlap(a, g), [line(s, y)]),
            ]
        return behavior

    # small letter o
    entry("o", [(MEDIUM, [circle(m, unit1_5, False)]),
                (MEDIUM, [line(k, o)]),
                (WEAK, [line(c, w)]),
                (WEAK, [line(a, y), line(u, e)])])(_round_bullet(unit1_5))

    # big letter O
    entry("O", [(MEDIUM, [circle(m, unit2, False)]),
                (MEDIUM, [line(k, o)]),
                (WEAK, [line(c, w)]),
                (WEAK, [line(a, y), line(u, e)])])(_round_bullet(unit2))

    # underscore _
    @entry("_", [(STRONG, [line(u, y)])])
    def _underscore(top_left, top, top_right, left, right, bottom_left, bottom,
                    bottom_right):
        return [
            (True, [line(u, y)]),
            #   /_
            (left.line_strongly_overlap(e, u), [line(u, cell.left().u())]),
            #   _\
            (right.line_strongly_overlap(a, y), [line(y, cell.right().gy())]),
        ]

    # dot period .
    @entry(".", [(MEDIUM, [line(m, w)]),
                 (WEAK, [line(m, k)]),
                 (WEAK, [line(m, o)])])
    def _dot(top_left, top, top_right, left, right, bottom_left, bottom,
             bottom_right):
        return [
            # .
            # |
            (bottom.line_strongly_overlap(c, h), [line(r, w)]),
            #   .
            #  / \
            (bottom_left.line_strongly_overlap(e, i)
             and bottom_right.line_strongly_overlap(a, g),
             [line(m, u), line(m, y)]),
            #  .-
            #  |
            (right.line_overlap(k, l) and bottom.line_overlap(c, h),
             [arc(o, r, unit2), line(r, w)]),
            #   .-
            #  |
            (right.line_overlap(k, l) and bottom_left.line_overlap(c, h),
             [arc(m, cell.bottom_left().c(), unit4), line(m, o)]),
            # -.
            #  |
            (left.line_overlap(n, o) and bottom.line_overlap(c, h),
             [arc(r, k, unit2), line(r, w)]),
            # -.
            #   |
            (not bottom_right.is_("`") and left.line_overlap(n, o)
             and bottom_right.line_overlap(c, h),
             [arc(cell.bottom_right().c(), m, unit4), line(k, m)]),
            #     .-
            #    /
            (right.line_overlap(k, l) and bottom_left.line_overlap(e, i),
             [arc(o, q, unit4), line(q, u)]),
            #     .-
            #      \
            (right.line_overlap(k, l) and bottom_right.line_overlap(a, g),
             [arc(o, s, between1_2), line(s, y)]),
            #     -.
            #       \
            (left.line_overlap(n, o) and bottom_right.line_overlap(a, g),
             [arc(s, k, unit4), line(s, y)]),
            #     -.
            #     /
            (left.line_overlap(n, o) and bottom_left.line_overlap(e, i),
             [arc(q, k, between1_2), line(u, q)]),
            #   .
            #  (
            (bottom_left.arcs_to(e, y), [arc(o, q, unit4), line(q, u)]),
            #  .
            #   )
            (bottom_right.arcs_to(u, a), [arc(s, k, unit4), line(s, y)]),
            #   _.-
            (left.line_overlap(u, y) and right.line_overlap(k, o),
             [line(u, o)]),
            #   -._
            (left.line_overlap(k, o) and right.line_overlap(u, y),
             [line(k, y)]),
            # `.
            #   `
            (left.is_("`") and bottom_right.is_("`"),
             [broken_line(cell.left().c(), cell.bottom_right().c())]),
            #   .'
            #  '
            (right.is_("'") and bottom_left.is_("'"),
             [broken_line(cell.right().c(), cell.bottom_left().c())]),
            # '.   `.
            #   \    \
            ((left.is_("'") or left.is_("`"))
             and bottom_right.line_overlap(a, m),
             [arc(y, cell.left().a(), unit8 * 2.0)]),
            #   .'
            #  /
            (right.is_("'") and bottom_left.line_overlap(e, m),
             [arc(cell.right().e(), u, unit8 * 2.0)]),
            #     |
            #     .
            #    /
            (top.line_overlap(m, w) and bottom_left.line_overlap(e, m),
             [arc(q, h, unit8), line(c, h), line(q, u)]),
            #      /
            #     .
            #    /
            (top_right.line_overlap(m, u) and bottom_left.line_overlap(e, m),
             [line(u, e)]),
            #   |
            #   .
            #    \
            (top.line_overlap(m, w) and bottom_right.line_overlap(a, m),
             [line(c, h), arc(h, s, unit8), line(s, y)]),
        ]

    # comma ,
    @entry(",", [(MEDIUM, [line(m, r)]),
                 (WEAK, [line(m, k)]),
                 (WEAK, [line(m, o)])])
    def _comma(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [
            #  ,-
            #  |
            (right.line_overlap(k, l) and bottom.line_overlap(c, h),
             [arc(o, r, unit2), line(r, w)]),
            #     ,-
            #    /
            (right.line_overlap(k, l) and bottom_left.line_overlap(e, i),
             [arc(o, q, unit4), line(q, u)]),
            #   ,
            #  (
            (bottom_left.arcs_to(e, y), [arc(o, q, unit4), line(q, u)]),
        ]

    # single quote '
    @entry("'", [(MEDIUM, [line(c, h)]),
                 (WEAK, [line(m, k)]),
                 (WEAK, [line(m, o)])])
    def _quote(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [
            #  |
            #  '
            (top.line_strongly_overlap(m, w), [line(c, h)]),
            #  |
            #  '-
            (right.line_overlap(k, l) and top.line_overlap(r, w),
             [arc(h, o, unit2), line(c, h)]),
            #  |
            #   '-
            (right.line_overlap(k, l) and top_left.line_overlap(r, w),
             [arc(cell.top_left().w(), m, unit4), line(m, o)]),
            #   |
            #  -'
            (left.line_overlap(n, o) and top.line_overlap(r, w),
             [arc(k, h, unit2), line(c, h)]),
            #    |
            #  -'
            (left.line_overlap(n, o) and top_right.line_overlap(r, w),
             [arc(m, cell.top_right().w(), unit4), line(k, m)]),
            #    \
            #     '-
            (top_left.line_overlap(s, y) and right.line_overlap(k, l),
             [line(a, g), arc(g, o, unit4)]),
            #      /
            #     '-
            (top_right.line_overlap(u, q) and right.line_overlap(k, l),
             [line(e, i), arc(i, o, between1_2)]),
            #       /
            #     -'
            (top_right.line_overlap(u, q) and left.line_overlap(n, o),
             [arc(k, i, unit4), line(i, e)]),
            #     \
            #     -'
            (top_left.line_overlap(s, y) and left.line_overlap(n, o),
             [arc(k, g, between1_2), line(g, a)]),
            #     \ /
            #      '
            (top_left.line_overlap(s, y) and top_right.line_overlap(u, q),
             [line(a, m), line(m, e)]),
            #  (
            #   '
            (top_left.arcs_to(e, y), [line(a, g), arc(g, o, unit4)]),
            #   )
            #  '
            (top_right.arcs_to(u, a), [arc(k, i, unit4), line(i, e)]),
            #    _
            #  -'
            (left.line_overlap(k, o) and top_right.line_overlap(u, y),
             [line(k, e)]),
            #  _
            #   '-
            (top_left.line_overlap(u, y) and right.line_overlap(k, o),
             [line(a, o)]),
            #    .
            #  .'
            (left.is_(".") and top_right.is_("."),
             [broken_line(cell.left().m(), cell.top_right().m())]),
            #  .
            #   '.
            (right.is_(".") and top_left.is_("."),
             [broken_line(cell.top_left().m(), cell.right().m())]),
            #    /
            #  .'
            (left.is_(".") and top_right.is_("/"),
             [arc(cell.left().u(), e, unit8 * 2.0)]),
        ]

    # other single quote U+2019
    @entry("’", [(MEDIUM, [line(c, h)]),
                      (WEAK, [line(m, k)]),
                      (WEAK, [line(m, o)])])
    def _right_quote(top_left, top, top_right, left, right, bottom_left,
                     bottom, bottom_right):
        return [
            (right.line_overlap(k, l) and top.line_overlap(r, w),
             [arc(h, o, unit2), line(c, h)]),
            (left.line_overlap(n, o) and top.line_overlap(r, w),
             [arc(k, h, unit2), line(c, h)]),
            (top_left.line_overlap(s, y) and right.line_overlap(k, l),
             [line(a, g), arc(g, o, unit4)]),
            (top_right.line_overlap(u, q) and right.line_overlap(k, l),
             [line(e, i), arc(i, o, between1_2)]),
            (top_right.line_overlap(u, q) and left.line_overlap(n, o),
             [arc(k, i, unit4), line(i, e)]),
            (top_left.line_overlap(s, y) and left.line_overlap(n, o),
             [arc(k, g, between1_2), line(g, a)]),
            (top_left.line_overlap(s, y) and top_right.line_overlap(u, q),
             [line(a, m), line(m, e)]),
            (top_left.arcs_to(e, y), [line(a, g), arc(g, o, unit4)]),
            (top_right.arcs_to(u, a), [arc(k, i, unit4), line(i, e)]),
            (left.line_overlap(k, o) and top_right.line_overlap(u, y),
             [line(k, e)]),
            (top_left.line_overlap(u, y) and right.line_overlap(k, o),
             [line(a, o)]),
            (left.is_(".") and top_right.is_("."),
             [broken_line(cell.left().m(), cell.top_right().m())]),
            (right.is_(".") and top_left.is_("."),
             [broken_line(cell.top_left().m(), cell.right().m())]),
        ]

    # backtick / backquote `
    @entry("`", [(MEDIUM, [line(c, m)]),
                 (WEAK, [line(m, k)]),
                 (WEAK, [line(m, o)])])
    def _backtick(top_left, top, top_right, left, right, bottom_left, bottom,
                  bottom_right):
        return [
            #  |
            #  `-
            (right.line_overlap(k, l) and top.line_overlap(r, w),
             [arc(h, o, unit2), line(c, h)]),
            #    \
            #     `-
            (top_left.line_overlap(s, y) and right.line_overlap(k, l),
             [line(a, g), arc(g, o, unit4)]),
            #  (
            #   `
            (top_left.arcs_to(e, y), [line(a, g), arc(g, o, unit4)]),
            #  _
            #   `-
            (top_left.line_overlap(u, y) and right.line_overlap(k, o),
             [line(a, o)]),
            # .
            #  `.
            (top_left.is_(".") and right.is_("."),
             [broken_line(cell.top_left().m(), cell.right().m())]),
            #  \
            #   `.
            (top_left.is_("\\") and right.is_("."),
             [arc(a, cell.right().gy(), unit8 * 2.0)]),
            #  ,
            #  `-
            (top.is_(",") and right.line_overlap(k, l),
             [arc(h, o, unit2), line(c, h)]),
        ]

    # forward slash /
    @entry("/", [(STRONG, [line(u, e)])])
    def _slash(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [
            (not bottom.line_strongly_overlap(c, h), [line(u, e)]),
            #    /-
            (right.line_strongly_overlap(k, l), [line(m, o)]),
            #    -/
            (left.line_strongly_overlap(n, o), [line(m, k)]),
            #    /
            #    |
            (bottom.line_strongly_overlap(c, h), [line(e, m), line(m, w)]),
        ]

    # backward slash \
    @entry("\\", [(STRONG, [line(a, y)])])
    def _backslash(top_left, top, top_right, left, right, bottom_left, bottom,
                   bottom_right):
        return [
            (not bottom.is_("|"), [line(a, y)]),
            #    \
            #    |
            (bottom.line_overlap(c, m), [line(a, m), line(m, w)]),
            #    \-
            (right.line_strongly_overlap(k, l), [line(m, o)]),
            #    -\
            (left.line_strongly_overlap(n, o), [line(m, k)]),
        ]

    # open parenthesis (
    @entry("(", [(MEDIUM, [arc(e, y, unit8)])])
    def _open_paren(top_left, top, top_right, left, right, bottom_left, bottom,
                    bottom_right):
        return [
            (not top.line_overlap(r, w) and not bottom.line_overlap(c, h),
             [arc(e, y, unit8)]),
            #   |
            #   (
            #   |
            (bottom.line_overlap(c, h), [arc(c, w, unit6)]),
            #   -(-
            (left.line_overlap(m, o) and right.line_overlap(k, l),
             [line(k, o)]),
        ]

    # close parenthesis )
    @entry(")", [(MEDIUM, [arc(u, a, unit8)])])
    def _close_paren(top_left, top, top_right, left, right, bottom_left,
                     bottom, bottom_right):
        return [
            (not top.line_overlap(r, w) and not bottom.line_overlap(c, h),
             [arc(u, a, unit8)]),
            #   |
            #   )
            #   |
            (top.line_overlap(r, w) and bottom.line_overlap(c, h),
             [arc(w, c, unit6)]),
            #   -)-
            (left.line_overlap(m, o) and right.line_overlap(k, l),
             [line(k, o)]),
        ]

    # big letter V
    @entry("V", [(MEDIUM, [polygon([f, j, w], True, [ARROW_BOTTOM])]),
                 (WEAK, [line(m, w)])])
    def _big_v(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [
            #  |
            #  V
            (top.line_overlap(r, w),
             [polygon([f, j, w], True, [ARROW_BOTTOM]), line(c, h)]),
            # \
            #  V
            (top_left.line_overlap(s, y),
             [polygon([f.adjust_x(-0.5), s, d.adjust_y(0.5)], True,
                      [ARROW_BOTTOM_RIGHT]),
              line(a, g)]),
            #    /
            #   V
            (top_right.line_overlap(u, q),
             [polygon([j.adjust_x(0.5), q, b.adjust_y(0.5)], True,
                      [ARROW_BOTTOM_LEFT]),
              line(e, i)]),
            #  `.
            #    V
            (top_left.is_("."),
             [polygon([f, o, c], True, [ARROW_BOTTOM_RIGHT])]),
            #     .'
            #    V
            (top_right.is_("."),
             [polygon([j, k, c], True, [ARROW_BOTTOM_LEFT])]),
            #    V
            #    |
            (bottom.line_overlap(c, h), [line(a, w), line(w, e)]),
        ]

    # letter v
    @entry("v", [(MEDIUM, [polygon([f, j, w], True,
                                   [ARROW_BOTTOM, ARROW_BOTTOM_LEFT,
                                    ARROW_BOTTOM_RIGHT])])])
    def _small_v(top_left, top, top_right, left, right, bottom_left, bottom,
                 bottom_right):
        return [
            # |
            # v
            (top.line_overlap(r, w),
             [polygon([f, j, w], True, [ARROW_BOTTOM]), line(c, h)]),
            # \
            #  v
            (top_left.line_overlap(s, y),
             [polygon([f.adjust_x(-0.5), s, d.adjust_y(0.5)], True,
                      [ARROW_BOTTOM_RIGHT]),
              line(a, g)]),
            #    /
            #   v
            (top_right.line_overlap(u, q),
             [polygon([j.adjust_x(0.5), q, b.adjust_y(0.5)], True,
                      [ARROW_BOTTOM_LEFT]),
              line(e, i)]),
            #  `.
            #    v
            (top_left.is_("."),
             [polygon([f, o, c], True, [ARROW_BOTTOM_RIGHT])]),
            #     .'
            #    v
            (top_right.is_("."),
             [polygon([j, k, c], True, [ARROW_BOTTOM_LEFT])]),
            #    v
            #    |
            (bottom.line_overlap(c, h) and not top.line_overlap(r, w),
             [line(a, w), line(w, e)]),
        ]

    # caret ^
    @entry("^", [(MEDIUM, [polygon([p, c, t], True,
                                   [ARROW_TOP, ARROW_TOP_LEFT,
                                    ARROW_TOP_RIGHT])])])
    def _caret(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [
            #   ^
            #   |
            (bottom.line_overlap(c, h),
             [polygon([p, c, t], True, [ARROW_TOP]), line(r, w)]),
            #  ^
            #   \
            (bottom_right.line_overlap(a, g) and not bottom_left.is_("/"),
             [polygon([t.adjust_x(0.5), g, v.adjust_y(-0.5)], True,
                      [ARROW_TOP_LEFT]),
              line(s, y)]),
            #   ^
            #  /
            (bottom_left.line_overlap(e, i) and not bottom_right.is_("\\"),
             [polygon([p.adjust_x(-0.5), i, x.adjust_y(-0.5)], True,
                      [ARROW_TOP_RIGHT]),
              line(u, q)]),
            #   |
            #   ^
            (top.line_overlap(r, w) and not bottom.line_overlap(c, h),
             [line(c, u), line(c, y)]),
            #   ^
            #  / \
            (bottom_left.is_("/") and bottom_right.is_("\\"),
             [line(c, u), line(c, y)]),
        ]

    # greater than >
    @entry(">", [(MEDIUM, [polygon([f, o, p], True, [ARROW_RIGHT])])])
    def _greater(top_left, top, top_right, left, right, bottom_left, bottom,
                 bottom_right):
        return [
            #   --->
            (left.line_overlap(n, o),
             [polygon([f, o, p], True, [ARROW_RIGHT])]),
            #   >----
            (right.line_overlap(k, l) and not left.line_overlap(n, o),
             [line(f, o), line(o, p)]),
            #  `>
            (left.is_("`"), [polygon([f, o, p], True, [ARROW_RIGHT])]),
            #  .>
            (left.is_("."), [polygon([f, o, p], True, [ARROW_RIGHT])]),
            # >>  (double arrow)
            (left.is_(">"), [polygon([f, o, p], True, [ARROW_RIGHT])]),
        ]

    # less than <
    @entry("<", [(MEDIUM, [polygon([j, k, t], True, [ARROW_LEFT])])])
    def _less(top_left, top, top_right, left, right, bottom_left, bottom,
              bottom_right):
        return [
            #    <--
            (right.line_overlap(k, l),
             [polygon([j, k, t], True, [ARROW_LEFT])]),
            #     --<
            (left.line_overlap(m, o) and not right.line_overlap(k, l),
             [line(j, k), line(k, t)]),
            #  <.
            (right.is_("."), [polygon([j, k, t], True, [ARROW_LEFT])]),
            #  <'
            (right.is_("'"), [polygon([j, k, t], True, [ARROW_LEFT])]),
            #  <<
            (right.is_("<"), [polygon([j, k, t], True, [ARROW_LEFT])]),
        ]

    # equal sign =
    @entry("=", [(MEDIUM, [line(_03, _43), line(_05, _45)])])
    def _equal(top_left, top, top_right, left, right, bottom_left, bottom,
               bottom_right):
        return [(True, [line(_03, _43), line(_05, _45)])]

    props = {}
    for ch, signature, behavior in table:
        props[ch] = Property(ch, signature, behavior)
    return props


ASCII_PROPERTIES = _build()
