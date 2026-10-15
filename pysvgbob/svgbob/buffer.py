"""Buffers and the ascii -> fragments -> svg pipeline (``buffer/*.rs``)."""

import unicodedata

from . import f32 as F
from .f32 import mul
from .geom import Cell
from .fragment import Arc, Rect, CellText, cell_text, rust_sort
from .property import EMPTY, property_from_char
from .parser import parse_css_legend, line_parse, ParseError
from .svg import Element, Text as TextNode

# characters with the Unicode White_Space property (Rust char::is_whitespace)
_RUST_WHITESPACE = frozenset(
    "\t\n\x0b\x0c\r \x85\xa0       "
    "         　")


def is_whitespace(ch):
    return ch in _RUST_WHITESPACE


def char_width(ch):
    """Display width of a char like ``unicode-width`` 0.1 (None = control)."""
    cp = ord(ch)
    if cp == 0:
        return 0
    if cp < 0x20:
        return None
    if cp < 0x7F:
        return 1
    if cp < 0xA0:
        return None
    if cp == 0xAD:  # soft hyphen
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    if unicodedata.category(ch) in ("Mn", "Me", "Cf") or 0x1160 <= cp <= 0x11FF:
        return 0
    return 1


_ALEF = frozenset("آأإاٱٲٳٵݳݴ")
_LAM = frozenset("لڵڶڷڸݪࢦ")


def _starts_emoji_presentation(ch):
    """Approximation of the bases of emoji variation sequences."""
    if ch in "#*0123456789":
        return True
    cp = ord(ch)
    if cp < 0xA9:
        return False
    if cp in (0xA9, 0xAE, 0x203C, 0x2049, 0x2122, 0x2139, 0x24C2, 0x3030,
              0x303D, 0x3297, 0x3299):
        return True
    return unicodedata.category(ch) == "So" and (0x2190 <= cp <= 0x2BFF
                                                 or cp >= 0x1F000)


def str_width(s):
    """``UnicodeWidthStr::width`` of unicode-width 0.1.14.

    Unlike the char width, control characters (including the ``\\0``
    padding after wide chars) count as 1.  A char followed by U+FE0F is an
    emoji (width 2) and an Arabic lam followed by alef is a single cell.
    """
    total = 0
    next_emoji = False
    next_alef = False
    for ch in reversed(s):
        if next_emoji:
            next_emoji = False
            if _starts_emoji_presentation(ch):
                total += 2
                next_alef = False
                continue
        if ord(ch) <= 0xA0:
            total += 1
            next_alef = False
            continue
        if ch == "️":
            next_emoji = True
            continue
        if next_alef:
            if ch in _LAM:
                next_alef = False
                continue
            if unicodedata.category(ch) == "Mn":
                continue
        if ch in _ALEF:
            next_alef = True
            total += 1
            continue
        next_alef = False
        total += char_width(ch) or 0
    return total


def rust_lines(s):
    """``str::lines``: split on ``\\n``, strip one trailing ``\\r`` per line,
    and drop the empty string after a final line ending."""
    if s == "":
        return []
    parts = s.split("\n")
    if parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]


def merge_recursive(items, merge):
    """``Merge::merge_recursive``: merge until the length stops shrinking."""
    items = list(items)
    while True:
        original_len = len(items)
        merged = second_pass_merge(items, merge)
        if len(merged) < original_len:
            items = merged
        else:
            return merged


def second_pass_merge(items, merge):
    new_groups = []
    for item in items:
        for idx in range(len(new_groups) - 1, -1, -1):
            merged = merge(new_groups[idx], item)
            if merged is not None:
                new_groups[idx] = merged
                break
        else:
            new_groups.append(item)
    return new_groups


def string_buffer_from_str(s):
    """``StringBuffer::from``: rows of chars, wide chars padded with ``\\0``."""
    rows = []
    for line in rust_lines(s):
        row = []
        for ch in line:
            row.append(ch)
            width = char_width(ch)
            if width is not None and width > 1:
                row.extend("\0" * (width - 1))
        rows.append(row)
    return rows


###########################################################################
# Span
###########################################################################

class Span(object):
    """A group of adjacent (cell, char) pairs."""

    __slots__ = ("items", "_cellset", "_bbox")

    def __init__(self, items):
        self.items = items
        self._cellset = None
        self._bbox = None

    def __eq__(self, other):
        return self.items == other.items

    def __ne__(self, other):
        return self.items != other.items

    __hash__ = None

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def _cells(self):
        if self._cellset is None:
            self._cellset = set(cell for cell, _ in self.items)
        return self._cellset

    def _yx_bbox(self):
        if self._bbox is None:
            ys = [cell[0] for cell, _ in self.items]
            xs = [cell[1] for cell, _ in self.items]
            self._bbox = (min(ys), min(xs), max(ys), max(xs))
        return self._bbox

    def can_merge(self, other):
        """True if any cell of this span is adjacent to any cell of ``other``."""
        if not self.items or not other.items:
            return False
        ay0, ax0, ay1, ax1 = self._yx_bbox()
        by0, bx0, by1, bx1 = other._yx_bbox()
        if ay0 > by1 + 1 or by0 > ay1 + 1 or ax0 > bx1 + 1 or bx0 > ax1 + 1:
            return False
        mine = self._cells()
        theirs = other._cells()
        if len(theirs) > len(mine):
            mine, theirs = theirs, mine
        for (cy, cx) in theirs:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (cy + dy, cx + dx) in mine:
                        return True
        return False

    def merge_no_check(self, other):
        span = Span(self.items + other.items)
        if self._bbox is not None and other._bbox is not None:
            a, b = self._bbox, other._bbox
            span._bbox = (min(a[0], b[0]), min(a[1], b[1]),
                          max(a[2], b[2]), max(a[3], b[3]))
        return span

    def merge(self, other):
        if self.can_merge(other):
            return self.merge_no_check(other)
        return None

    def bounds(self):
        if not self.items:
            return None
        xs = [cell[1] for cell, _ in self.items]
        ys = [cell[0] for cell, _ in self.items]
        return Cell(min(xs), min(ys)), Cell(max(xs), max(ys))

    def localize(self):
        bounds = self.bounds()
        if bounds is None:
            return self
        tl = bounds[0]
        return Span([(tl.localize_cell(cell), ch) for cell, ch in self.items])

    def extract(self, bound1, bound2):
        return Span([(cell, ch) for cell, ch in self.items
                     if cell.is_bounded(bound1, bound2)])

    def endorse(self):
        """Endorse into circles/arcs, then rects; returns (accepted, rejects)."""
        accepted, un_endorsed_span = self.endorse_to_arcs_and_circles()
        un_endorsed_contacts = contacts_from_span(un_endorsed_span)
        rect_accepted, rect_rejects = endorse_rects(un_endorsed_contacts)
        accepted.extend(rect_accepted)
        re_accepted, re_rejects = Span.re_endorse(rect_rejects)
        accepted.extend(re_accepted)
        return accepted, re_rejects

    @staticmethod
    def re_endorse(rect_rejects):
        span_rejects = [contact.span() for contact in rect_rejects]
        span_rejects = merge_recursive(span_rejects, Span.merge)
        accepted = []
        rejects = []
        for span in span_rejects:
            acc, rej = span.endorse_to_arcs_and_circles()
            accepted.extend(acc)
            rejects.append(rej)
        return accepted, rejects

    def endorse_to_arcs_and_circles(self):
        from . import circle_map
        accepted = []
        top_left = self.bounds()[0]
        for finder in (circle_map.endorse_circle_span,
                       circle_map.endorse_three_quarters_arc_span,
                       circle_map.endorse_half_arc_span,
                       circle_map.endorse_quarter_arc_span):
            found = finder(self)
            if found is not None:
                frag, un_endorsed_span = found
                frag = frag.absolute_position(top_left)
                accepted.append(FragmentSpan(Span(list(self.items)), frag))
                return accepted, un_endorsed_span
        return accepted, self


###########################################################################
# FragmentSpan, Contacts, FragmentBuffer, PropertyBuffer
###########################################################################

class FragmentSpan(object):
    __slots__ = ("span", "fragment")

    def __init__(self, span, fragment):
        self.span = span
        self.fragment = fragment

    def __eq__(self, other):
        return self.span == other.span and self.fragment == other.fragment

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None

    def __repr__(self):
        return "FragmentSpan(%r)" % (self.fragment,)

    def scale(self, scale):
        return FragmentSpan(self.span, self.fragment.scale(scale))

    def absolute_position(self, cell):
        return FragmentSpan(self.span, self.fragment.absolute_position(cell))

    def is_contacting(self, other):
        return self.fragment.is_contacting(other.fragment)

    def merge(self, other):
        new_merge = self.fragment.merge(other.fragment)
        if new_merge is not None:
            return FragmentSpan(self.span.merge_no_check(other.span), new_merge)
        return None


def fragment_span_from_cell_text(ct):
    """``impl From<CellText> for FragmentSpan``."""
    cells = [(Cell(ct.start.x + i, ct.start.y), ch)
             for i, ch in enumerate(ct.content)]
    return FragmentSpan(Span(cells), ct)


class Contacts(object):
    """A group of fragments that touch each other."""

    __slots__ = ("frags",)

    def __init__(self, frags):
        self.frags = frags

    def fragments(self):
        return [fs.fragment for fs in self.frags]

    def span(self):
        items = []
        for fs in self.frags:
            items.extend(fs.span.items)
        return Span(items)

    def is_contacting(self, other):
        mine = self.frags
        for other_frag in other.frags:
            of = other_frag.fragment
            for frag in reversed(mine):
                if frag.fragment.is_contacting(of):
                    return True
        return False

    def merge(self, other):
        if self.is_contacting(other):
            return Contacts(self.frags + other.frags)
        return None

    def endorse_rect(self):
        fragments = self.fragments()
        rect = endorse_rect(fragments)
        if rect is not None:
            return rect
        return endorse_rounded_rect(fragments)


def endorse_rects(contacts):
    accepted = []
    rejects = []
    for contact in contacts:
        fragment = contact.endorse_rect()
        if fragment is not None:
            accepted.append(FragmentSpan(contact.span(), fragment))
        else:
            rejects.append(contact)
    return accepted, rejects


def contacts_from_span(span):
    """``impl From<Span> for Vec<Contacts>``."""
    fb = fragment_buffer_from_span(span)
    merged = fb.merge_fragment_spans()
    contacts = [Contacts([fs]) for fs in merged]
    return merge_recursive(contacts, Contacts.merge)


def merge_fragments(fragments):
    return merge_recursive(fragments, lambda a, b: a.merge(b))


class FragmentBuffer(object):
    __slots__ = ("cells",)

    def __init__(self):
        self.cells = {}

    def _sort_cell(self, cell):
        frags = self.cells.get(cell)
        if frags is not None:
            rust_sort(frags, lambda a, b: a.fragment < b.fragment)

    def add_fragment_span_to_cell(self, cell, fragment_span):
        existing = self.cells.get(cell)
        if existing is not None:
            if fragment_span not in existing:
                existing.append(fragment_span)
        else:
            self.cells[cell] = [fragment_span]
        self._sort_cell(cell)

    def add_fragment_to_cell(self, cell, ch, fragment):
        self.add_fragment_span_to_cell(
            cell, FragmentSpan(Span([(cell, ch)]), fragment))

    def add_fragments_to_cell(self, cell, ch, fragments):
        spans = [FragmentSpan(Span([(cell, ch)]), frag) for frag in fragments]
        existing = self.cells.get(cell)
        if existing is not None:
            existing.extend(spans)
        else:
            self.cells[cell] = spans
        self._sort_cell(cell)

    def abs_fragment_spans(self):
        out = []
        for cell in sorted(self.cells):
            for fs in self.cells[cell]:
                out.append(fs.absolute_position(cell))
        return out

    def merge_fragment_spans(self):
        return merge_recursive(self.abs_fragment_spans(), FragmentSpan.merge)


def _neighbors(pb, cell):
    y, x = cell
    get = pb.get
    return (get(Cell(x - 1, y - 1), EMPTY), get(Cell(x, y - 1), EMPTY),
            get(Cell(x + 1, y - 1), EMPTY), get(Cell(x - 1, y), EMPTY),
            get(Cell(x + 1, y), EMPTY), get(Cell(x - 1, y + 1), EMPTY),
            get(Cell(x, y + 1), EMPTY), get(Cell(x + 1, y + 1), EMPTY))


def fragment_buffer_from_property_buffer(pb):
    from .unicode_map import UNICODE_FRAGMENTS
    fb = FragmentBuffer()
    for cell, prop in pb.items():
        cell_fragments = prop.fragments(*_neighbors(pb, cell))
        if cell_fragments:
            fb.add_fragments_to_cell(cell, prop.ch, cell_fragments)
        else:
            frags = UNICODE_FRAGMENTS.get(prop.ch)
            if frags is not None:
                fb.add_fragments_to_cell(cell, prop.ch,
                                         merge_fragments(list(frags)))
            else:
                fb.add_fragment_to_cell(cell, prop.ch, cell_text(prop.ch))
    return fb


def property_buffer_from_span(span):
    pb = {}
    for cell, ch in span.items:
        prop = property_from_char(ch)
        if prop is not None:
            pb[cell] = prop
    return pb


def fragment_buffer_from_span(span):
    """``impl From<Span> for FragmentBuffer``."""
    from .unicode_map import UNICODE_FRAGMENTS
    pb = property_buffer_from_span(span)
    fb = fragment_buffer_from_property_buffer(pb)
    for cell, ch in span.items:
        if cell not in pb:
            frags = UNICODE_FRAGMENTS.get(ch)
            if frags is not None:
                fb.add_fragments_to_cell(cell, ch, list(frags))
            else:
                fb.add_fragment_to_cell(cell, ch, cell_text(ch))
    return fb


###########################################################################
# endorse: promote groups of fragments into rects and rounded rects
###########################################################################

def _min_max_points(fragments):
    lo = hi = None
    for frag in fragments:
        for p in frag.bounds():
            if lo is None or p.cmp(lo) < 0:
                lo = p
            if hi is None or p.cmp(hi) >= 0:
                hi = p
    return lo, hi


def parallel_aabb_group(fragments):
    parallels = []
    for index1, frag1 in enumerate(fragments):
        for index2, frag2 in enumerate(fragments):
            if (index1 != index2
                    and not any(index1 == p1 or index1 == p2
                                or index2 == p1 or index2 == p2
                                for p1, p2 in parallels)
                    and frag1.is_aabb_parallel(frag2)):
                parallels.append((index1, index2))
    return parallels


def is_rect(fragments):
    if len(fragments) != 4:
        return False
    parallels = parallel_aabb_group(fragments)
    if len(parallels) != 2:
        return False
    (a1, a2), (b1, b2) = parallels
    return (fragments[a1].is_touching_aabb_perpendicular(fragments[b1])
            and fragments[a2].is_touching_aabb_perpendicular(fragments[b2]))


def endorse_rect(fragments):
    if is_rect(fragments):
        is_any_broken = any(frag.is_broken() for frag in fragments)
        lo, hi = _min_max_points(fragments)
        return Rect(lo, hi, False, is_any_broken)
    return None


def right_angle_arcs(fragments):
    return [index for index, frag in enumerate(fragments)
            if type(frag) is Arc and frag.is_aabb_right_angle_arc()]


def is_rounded_rect(fragments):
    if len(fragments) != 8:
        return False, None
    parallels = parallel_aabb_group(fragments)
    right_arcs = right_angle_arcs(fragments)
    if len(parallels) == 2 and len(right_arcs) == 4:
        arc_radius = fragments[right_arcs[0]].radius
        (a1, a2), (b1, b2) = parallels
        passed = (fragments[a1].is_aabb_perpendicular(fragments[b1])
                  and fragments[a2].is_aabb_perpendicular(fragments[b2]))
        return passed, arc_radius
    return False, None


def endorse_rounded_rect(fragments):
    passed, arc_radius = is_rounded_rect(fragments)
    if passed:
        is_any_broken = any(frag.is_broken() for frag in fragments)
        lo, hi = _min_max_points(fragments)
        return Rect(lo, hi, False, is_any_broken, arc_radius)
    return None


###########################################################################
# FragmentTree: nest fragments inside the shapes that contain them
###########################################################################

class FragmentTree(object):
    __slots__ = ("fragment", "css_tag", "enclosing", "box")

    def __init__(self, fragment):
        self.fragment = fragment
        self.css_tag = []
        self.enclosing = []
        tl, br = fragment.fragment.bounds()
        self.box = (tl.x, tl.y, br.x, br.y)

    def can_fit(self, other):
        x0, y0, x1, y1 = self.box
        ox0, oy0, ox1, oy1 = other.box
        return x0 <= ox0 and y0 <= oy0 and x1 >= ox1 and y1 >= oy1

    def enclose_deep_first(self, other):
        for child in self.enclosing:
            if child.enclose_deep_first(other):
                return True
        if self.can_fit(other):
            css_tags = other.fragment.fragment.as_css_tag()
            if css_tags:
                self.css_tag.extend(css_tags)
            else:
                self.enclosing.append(other)
            return True
        return False

    @staticmethod
    def enclose_recursive(trees):
        while True:
            original_len = len(trees)
            merged = []
            for tree in trees:
                for idx in range(len(merged) - 1, -1, -1):
                    if merged[idx].enclose_deep_first(tree):
                        break
                else:
                    merged.append(tree)
            if len(merged) < original_len:
                trees = merged
            else:
                return merged

    def into_nodes(self, out):
        node = self.fragment.fragment.to_node()
        node.attrs.append(("class", list(self.css_tag)))
        out.append(node)
        for child in self.enclosing:
            child.into_nodes(out)

    @staticmethod
    def fragments_to_node(fragments):
        trees = FragmentTree.enclose_recursive(
            [FragmentTree(frag) for frag in fragments])
        nodes = []
        for tree in trees:
            tree.into_nodes(nodes)
        return nodes


###########################################################################
# CellBuffer
###########################################################################

_MARKERS = (
    ("arrow", "-2 -2 8 8", "4", "2", "polygon", "0,0 0,4 4,2 0,0", None),
    ("diamond", "-2 -2 8 8", "4", "2", "polygon", "0,2 2,0 4,2 2,4 0,2", None),
    ("circle", "0 0 8 8", "4", "4", "circle", "2", "filled"),
    ("open_circle", "0 0 8 8", "4", "4", "circle", "2", "bg_filled"),
    ("big_open_circle", "0 0 8 8", "4", "4", "circle", "3", "bg_filled"),
)


def _defs():
    markers = []
    for mid, view_box, ref_x, ref_y, shape, arg, cls in _MARKERS:
        if shape == "polygon":
            child = Element("polygon", [("points", arg)])
        else:
            child = Element("circle", [("cx", "4"), ("cy", "4"), ("r", arg),
                                       ("class", cls)])
        markers.append(Element("marker", [
            ("id", mid), ("viewBox", view_box), ("refX", ref_x),
            ("refY", ref_y), ("markerWidth", "7"), ("markerHeight", "7"),
            ("orient", "auto-start-reverse"),
        ], [child]))
    return Element("defs", [], markers)


def _jss(rules):
    blocks = []
    for selector, props in rules:
        body = "".join("  %s: %s;\n" % (name, value) for name, value in props)
        blocks.append("%s {\n%s}\n" % (selector, body))
    return "\n".join(blocks)


def _style(settings, legend_css):
    stroke_color = settings.stroke_color
    background = settings.background
    rules = [
        (".svgbob line, .svgbob path, .svgbob circle, .svgbob rect, .svgbob polygon", [
            ("stroke", stroke_color),
            ("stroke-width", F.fmt(settings.stroke_width)),
            ("stroke-opacity", "1"),
            ("fill-opacity", "1"),
            ("stroke-linecap", "round"),
            ("stroke-linejoin", "miter"),
        ]),
        (".svgbob text", [
            ("white-space", "pre"),
            ("fill", stroke_color),
            ("font-family", settings.font_family),
            ("font-size", "%dpx" % settings.font_size),
        ]),
        (".svgbob rect.backdrop", [
            ("stroke", "none"),
            ("fill", background),
        ]),
        (".svgbob .broken", [("stroke-dasharray", "8")]),
        (".svgbob .filled", [("fill", settings.fill_color)]),
        (".svgbob .bg_filled", [("fill", background), ("stroke-width", "1")]),
        (".svgbob .nofill", [("fill", background)]),
        (".svgbob .end_marked_arrow", [("marker-end", "url(#arrow)")]),
        (".svgbob .start_marked_arrow", [("marker-start", "url(#arrow)")]),
        (".svgbob .end_marked_diamond", [("marker-end", "url(#diamond)")]),
        (".svgbob .start_marked_diamond", [("marker-start", "url(#diamond)")]),
        (".svgbob .end_marked_circle", [("marker-end", "url(#circle)")]),
        (".svgbob .start_marked_circle", [("marker-start", "url(#circle)")]),
        (".svgbob .end_marked_open_circle", [("marker-end", "url(#open_circle)")]),
        (".svgbob .start_marked_open_circle", [("marker-start", "url(#open_circle)")]),
        (".svgbob .end_marked_big_open_circle", [("marker-end", "url(#big_open_circle)")]),
        (".svgbob .start_marked_big_open_circle", [("marker-start", "url(#big_open_circle)")]),
    ]
    css = "\n".join([_jss(rules), legend_css])
    return Element("style", [], [TextNode(css)])


class CellBuffer(object):
    """Maps each non-blank cell to its character, plus legend and texts."""

    def __init__(self):
        self.map = {}
        self.css_styles = []
        self.escaped_text = []

    @staticmethod
    def from_str(text):
        loc = text.find("# Legend:")
        if loc >= 0:
            try:
                css_styles = parse_css_legend(text[loc:])
            except ParseError:
                css_styles = None
            if css_styles is not None:
                cb = CellBuffer.from_string_buffer(string_buffer_from_str(text[:loc]))
                cb.css_styles.extend(css_styles)
                return cb
        return CellBuffer.from_string_buffer(string_buffer_from_str(text))

    @staticmethod
    def from_string_buffer(rows):
        cb = CellBuffer()
        for y, line in enumerate(rows):
            line_str = "".join(line)
            escaped_text, unescaped = CellBuffer.escape_line(y, line_str)
            cb.escaped_text.extend(escaped_text)
            for x, ch in enumerate(unescaped):
                if ch != "\0" and not is_whitespace(ch):
                    cb.map[Cell(x, y)] = ch
        return cb

    @staticmethod
    def escape_line(line, raw):
        input_chars = list(raw)
        char_locs = line_parse(input_chars)
        if not char_locs:
            return [], raw
        escaped_text = []
        parts = []
        index = 0
        for start, end in char_locs:
            escaped = "".join(input_chars[start + 1:end])
            width = str_width(escaped)
            escaped_text.append((Cell(start, line), escaped))
            parts.append("".join(input_chars[index:start]))
            parts.append(" " * (width + 2))
            index = end + 1
        parts.append("".join(input_chars[index:]))
        return escaped_text, "".join(parts)

    def bounds(self):
        if not self.map:
            return None
        xs = [cell[1] for cell in self.map]
        ys = [cell[0] for cell in self.map]
        return Cell(min(xs), min(ys)), Cell(max(xs), max(ys))

    def spans(self):
        """Group adjacent cells together (``impl From<&CellBuffer> for Vec<Span>``)."""
        spans = [Span([(cell, self.map[cell])]) for cell in sorted(self.map)]
        return merge_recursive(spans, Span.merge)

    def get_size(self, settings):
        bounds = self.bounds()
        bottom_right = bounds[1] if bounds is not None else Cell(0, 0)
        w = mul(mul(settings.scale, float(bottom_right.x + 2)), Cell.width())
        h = mul(mul(settings.scale, float(bottom_right.y + 2)), Cell.height())
        return w, h

    def legend_css(self):
        return "\n".join(".svgbob .%s{ %s }" % (cls, styles)
                         for cls, styles in self.css_styles)

    def escaped_text_nodes(self):
        return [fragment_span_from_cell_text(CellText(cell, text))
                for cell, text in self.escaped_text]

    def endorse_to_fragment_spans(self):
        """Returns (accepted fragment spans, groups of touching fragments)."""
        endorsed = []
        all_contacts = []
        for span in self.spans():
            accepted, rejects = span.endorse()
            endorsed.extend(accepted)
            for reject in rejects:
                all_contacts.extend(contacts_from_span(reject))
        singles = []
        groups = []
        for contacts in all_contacts:
            if len(contacts.frags) == 1:
                singles.extend(contacts.frags)
            else:
                groups.append(list(contacts.frags))
        return endorsed + singles, groups

    def group_nodes_and_fragments(self, settings):
        escaped = self.escaped_text_nodes()
        accepted, rejects = self.endorse_to_fragment_spans()
        group_nodes = [
            Element("g", [], [fs.scale(settings.scale).fragment.to_node()
                              for fs in fragments])
            for fragments in rejects
        ]
        return group_nodes, accepted + escaped

    def get_node_with_size(self, settings):
        w, h = self.get_size(settings)
        legend_css = self.legend_css()
        group_nodes, fragments = self.group_nodes_and_fragments(settings)
        node = CellBuffer.fragments_to_node(fragments, legend_css, settings, w, h)
        return node.with_children(group_nodes), w, h

    def get_node_override_size(self, settings, w, h):
        legend_css = self.legend_css()
        group_nodes, fragments = self.group_nodes_and_fragments(settings)
        node = CellBuffer.fragments_to_node(fragments, legend_css, settings, w, h)
        return node.with_children(group_nodes)

    @staticmethod
    def fragments_to_node(fragments, legend_css, settings, w, h):
        scaled = [fs.scale(settings.scale) for fs in fragments]
        fragment_nodes = FragmentTree.fragments_to_node(scaled)
        children = []
        if settings.include_styles:
            children.append(_style(settings, legend_css))
        if settings.include_defs:
            children.append(_defs())
        if settings.include_backdrop:
            children.append(Element("rect", [
                ("class", "backdrop"), ("x", "0"), ("y", "0"),
                ("width", F.fmt(w)), ("height", F.fmt(h))]))
        children.extend(fragment_nodes)
        return Element("svg", [
            ("xmlns", "http://www.w3.org/2000/svg"),
            ("width", F.fmt(w)), ("height", F.fmt(h)),
            ("class", "svgbob"),
        ], children)
