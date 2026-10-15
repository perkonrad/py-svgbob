"""Character properties: the fragments a character draws in context."""

from .fragment import Line

# Signal intensities
FAINT = 1
WEAK = 2
MEDIUM = 3
STRONG = 4


class Property(object):
    """``Property``: signature fragments plus a context dependent behavior.

    ``behavior`` is called with the 8 neighbouring properties (top_left,
    top, top_right, left, right, bottom_left, bottom, bottom_right) and
    returns a list of (condition, [fragments]).
    """

    __slots__ = ("ch", "signature", "behavior")

    def __init__(self, ch, signature, behavior):
        self.ch = ch
        self.signature = signature
        self.behavior = behavior

    def __repr__(self):
        return "Property(%r)" % self.ch

    @staticmethod
    def with_strong_fragments(ch, fragments):
        frags = list(fragments)
        return Property(ch, [(STRONG, frags)],
                        lambda *_: [(True, list(frags))])

    def is_(self, ch):
        return self.ch == ch

    def line_overlap(self, a, b):
        return self._line_overlap_with_signal(a, b, MEDIUM)

    def line_strongly_overlap(self, a, b):
        return self._line_overlap_with_signal(a, b, STRONG)

    def line_weakly_overlap(self, a, b):
        return self._line_overlap_with_signal(a, b, WEAK)

    def _line_overlap_with_signal(self, a, b, required):
        for signal, frags in self.signature:
            if signal >= required:
                for frag in frags:
                    if type(frag) is Line and frag.overlaps(a, b):
                        return True
        return False

    def has_endpoint(self, p):
        return any(frag.has_endpoint(p)
                   for _, frags in self.signature for frag in frags)

    def arcs_to(self, a, b):
        return any(frag.arcs_to(a, b)
                   for _, frags in self.signature for frag in frags)

    def fragments(self, top_left, top, top_right, left, right, bottom_left,
                  bottom, bottom_right):
        out = []
        for passed, frags in self.behavior(top_left, top, top_right, left,
                                           right, bottom_left, bottom,
                                           bottom_right):
            if passed:
                out.extend(frags)
        return out


EMPTY = Property(" ", [], lambda *_: [])


def property_from_char(ch):
    """Look ``ch`` up in the ascii map, then in the unicode map."""
    from .ascii_map import ASCII_PROPERTIES
    from .unicode_map import UNICODE_PROPERTIES
    prop = ASCII_PROPERTIES.get(ch)
    if prop is None:
        prop = UNICODE_PROPERTIES.get(ch)
    return prop
