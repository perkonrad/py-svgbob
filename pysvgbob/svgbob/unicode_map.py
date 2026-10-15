"""Fragments of unicode box drawing characters (``map/unicode_map.rs``)."""

from .geom import Cell, CellGrid
from .fragment import (arc, broken_line, circle, line, polygon, rect,
                       sort_fragments, ARROW_BOTTOM, ARROW_LEFT, ARROW_RIGHT,
                       ARROW_TOP, DIAMOND_BULLET)
from .property import Property


def _build():
    G = CellGrid
    a, b, c, d, e = G.a(), G.b(), G.c(), G.d(), G.e()
    f, h, j = G.f(), G.h(), G.j()
    k, l, m, n, o = G.k(), G.l(), G.m(), G.n(), G.o()
    p, q, r, s, t = G.p(), G.q(), G.r(), G.s(), G.t()
    u, v, w, x, y = G.u(), G.v(), G.w(), G.x(), G.y()

    _01 = G.point(0, 1)
    _03 = G.point(0, 3)
    _43 = G.point(4, 3)
    _05 = G.point(0, 5)
    _45 = G.point(4, 5)

    unit1 = Cell.unit(1)
    unit2 = Cell.unit(2)
    unit4 = Cell.unit(4)

    entries = [
        # overline, U+203E
        ("‾", [line(a, e)]),
        # macron, U+00AF
        ("¯", [line(a, e)]),
        # dash
        ("─", [line(k, o)]),
        # en dash
        ("–", [line(k, o)]),
        # em dash
        ("—", [line(k, o)]),
        # broken horizontal line
        ("┄", [broken_line(k, o)]),
        # vertical line
        ("│", [line(c, w)]),
        # broken vertical lines
        ("╎", [broken_line(c, w)]),
        ("┊", [broken_line(c, w)]),
        ("┆", [broken_line(c, w)]),
        # slant left / right
        ("╲", [line(a, y)]),
        ("╱", [line(e, u)]),
        # X line
        ("╳", [line(a, y), line(e, u)]),
        # cross line, plus
        ("┼", [line(c, w), line(k, o)]),
        # parallel horizontal line, equal
        ("═", [line(_03, _43), line(_05, _45)]),
        # square box
        ("□", [line(a, e), line(d, x), line(y, u), line(b, v)]),
        # vertical line left / right
        ("▏", [line(b, v)]),
        ("▕", [line(d, x)]),
        # double vertical line
        ("║", [line(b, v), line(d, x)]),
        # angle left
        ("∠", [line(e, u), line(u, y)]),
        # angle top
        ("⋀", [line(u, c), line(c, y)]),
        # triangle
        ("△", [line(c, y), line(y, u), line(u, c)]),
        # arrows
        ("▾", [polygon([f, j, w], True, [ARROW_BOTTOM]), line(c, h)]),
        ("▼", [polygon([f, j, w], True, [ARROW_BOTTOM]), line(c, h)]),
        ("▴", [polygon([p, c, t], True, [ARROW_TOP]), line(r, w)]),
        ("▲", [polygon([p, c, t], True, [ARROW_TOP]), line(r, w)]),
        ("▸", [polygon([f, o, p], True, [ARROW_RIGHT])]),
        ("◂", [polygon([j, k, t], True, [ARROW_LEFT])]),
        ("▶", [polygon([f, o, p], True, [ARROW_RIGHT])]),
        ("►", [polygon([f, o, p], True, [ARROW_RIGHT])]),
        ("◀", [polygon([j, k, t], True, [ARROW_LEFT])]),
        ("◄", [polygon([j, k, t], True, [ARROW_LEFT])]),
        ("◆", [polygon([k, h, o, r, k], True, [DIAMOND_BULLET])]),
        ("▪", [rect(f, t, True, False)]),
        # block elements 1/8 .. 8/8
        ("▁", [rect(_01, y, True, False)]),
        ("▂", [rect(p, y, True, False)]),
        ("▃", [rect(_05, y, True, False)]),
        ("▄", [rect(k, y, True, False)]),
        ("▅", [rect(_03, y, True, False)]),
        ("▆", [rect(f, y, True, False)]),
        ("▇", [rect(_01, y, True, False)]),
        ("█", [rect(a, y, True, False)]),
        # L shape bottom-left box
        ("⌊", [line(a, u), line(u, w)]),
        # not equal sign
        ("≠", [line(_03, _43), line(_05, _45), line(e, u)]),
        # cross with double horizontal
        ("╪", [line(_03, _43), line(_05, _45), line(c, w)]),
        # cross with double vertical
        ("╫", [line(k, o), line(b, v), line(d, x)]),
        ("⊕", [line(c, w), line(k, o), circle(m, unit2, False)]),
        # Big O
        ("○", [circle(m, unit2, False)]),
        ("⦵", [circle(m, unit2, False), line(k, o)]),
        ("●", [circle(m, unit2, True)]),
        ("￮", [circle(m, unit1, True)]),
        ("┌", [line(m, o), line(m, w)]),
        ("┐", [line(m, k), line(m, w)]),
        ("┘", [line(c, m), line(k, m)]),
        ("└", [line(c, m), line(m, o)]),
        ("├", [line(c, w), line(m, o)]),
        ("┤", [line(c, w), line(k, m)]),
        ("┬", [line(k, o), line(m, w)]),
        ("┴", [line(k, o), line(c, m)]),
        # rounded corners
        ("╭", [arc(o, r, unit2), line(r, w)]),
        ("╮", [line(w, r), arc(r, k, unit2)]),
        ("╰", [line(c, h), arc(h, o, unit2)]),
        ("╯", [line(c, h), arc(k, h, unit2)]),
        ("◜", [arc(e, m, unit4), line(m, w)]),
        ("◝", [arc(m, a, unit4), line(m, w)]),
        ("◟", [arc(m, y, unit4), line(c, m)]),
        ("◞", [arc(u, m, unit4), line(m, c)]),
        ("║", [line(b, v), line(v, b), line(d, x), line(x, d)]),
        ("═", [line(k, o), line(p, t)]),
        ("╔", [line(o, l), line(l, v), line(t, s), line(s, x)]),
        ("╗", [line(k, n), line(n, x), line(p, q), line(q, v)]),
        ("╚", [line(b, q), line(q, t), line(d, n), line(n, o)]),
        ("╝", [line(p, s), line(s, d), line(k, l), line(l, b)]),
        ("╒", [line(m, w), line(m, o), line(r, t)]),
        ("╓", [line(l, o), line(l, v), line(n, x)]),
        ("╬", [line(b, l), line(l, k), line(p, q), line(q, v),
               line(d, n), line(n, o), line(t, s), line(s, x)]),
        ("╦", [line(k, o), line(p, q), line(q, v), line(t, s), line(s, x)]),
        ("╩", [line(p, t), line(k, l), line(l, b), line(d, n), line(n, o)]),
        ("╠", [line(b, v), line(d, n), line(n, o), line(t, s), line(s, x)]),
        ("╣", [line(d, x), line(b, l), line(l, k), line(p, q), line(q, v)]),
        ("╒", [line(m, w), line(m, o), line(r, t)]),
        ("╓", [line(l, o), line(l, v), line(n, x)]),
        ("╞", [line(c, w), line(m, o), line(r, t)]),
        ("╡", [line(c, w), line(k, m), line(p, r)]),
        ("╤", [line(k, o), line(p, t), line(r, w)]),
        ("╥", [line(k, o), line(l, v), line(n, x)]),
        ("╖", [line(k, n), line(n, x), line(l, v)]),
        ("╙", [line(l, o), line(l, b), line(n, d)]),
        ("╜", [line(k, n), line(l, b), line(n, d)]),
        ("╕", [line(m, w), line(k, m), line(p, r)]),
        ("╛", [line(c, r), line(r, p), line(k, m)]),
        ("╘", [line(c, r), line(m, o), line(r, t)]),
        ("╢", [line(d, x), line(b, v), line(k, l)]),
        ("╟", [line(d, x), line(b, v), line(n, o)]),
        ("╪", [line(c, w), line(k, o), line(p, t)]),
        ("╧", [line(k, o), line(p, t), line(c, m)]),
        ("╫", [line(k, o), line(b, v), line(d, x)]),
        ("╨", [line(k, o), line(b, l), line(d, n)]),
        ("⤹", [arc(j, r, unit2),
               polygon([y.adjust(-0.5, -0.5), r.adjust(0.5, -0.5),
                        r.adjust(-0.5, 0.5)], True, [])]),
    ]
    frags = {}
    for ch, fragments in entries:
        # later duplicates replace earlier ones, like BTreeMap::insert
        frags[ch] = sort_fragments(list(fragments))
    return dict(sorted(frags.items()))


UNICODE_FRAGMENTS = _build()

UNICODE_PROPERTIES = dict(
    (ch, Property.with_strong_fragments(ch, frags))
    for ch, frags in UNICODE_FRAGMENTS.items())
