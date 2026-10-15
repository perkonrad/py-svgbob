"""Hand-written equivalents of the pom parsers in ``util::parser``.

They reproduce the pom semantics, including the quirks:

* ``-space() * ident()`` is a look-ahead in pom, so leading spaces before
  a legend class name are *not* skipped and make the list stop.
* ``list()`` never fails, so a bare ``# Legend:`` line parses as a legend
  with no styles.
* identifier characters are tested on ``ch as u8`` (the low byte).
* ``parse()`` does not require the whole input to be consumed.
"""


class ParseError(Exception):
    pass


def _alpha(ch):
    b = ord(ch) & 0xFF
    return 0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A


def _digit(ch):
    b = ord(ch) & 0xFF
    return 0x30 <= b <= 0x39


def _ident_start(ch):
    return _alpha(ch) or ch == "_"


def _ident_rest(ch):
    return _alpha(ch) or _digit(ch) or ch == "_"


def _ident(s, pos):
    """Return (identifier, new_pos) or None."""
    if pos < len(s) and _ident_start(s[pos]):
        end = pos + 1
        while end < len(s) and _ident_rest(s[end]):
            end += 1
        return s[pos:end], end
    return None


def _space(s, pos):
    while pos < len(s) and s[pos] in " \t":
        pos += 1
    return pos


def parse_css_tag(text):
    """Parse ``{class1,class2}``; raise ParseError when it is not a tag."""
    s = text
    if not s.startswith("{"):
        raise ParseError("expect {")
    pos = 1
    items = []
    r = _ident(s, pos)
    if r is not None:
        items.append(r[0])
        pos = r[1]
        while pos < len(s) and s[pos] == ",":
            r = _ident(s, pos + 1)
            if r is None:
                break
            items.append(r[0])
            pos = r[1]
    if pos < len(s) and s[pos] == "}":
        return items
    raise ParseError("expect }")


def _css_styles(s, pos):
    """``{`` any chars except braces ``}`` -> (content, new_pos) or None."""
    if pos >= len(s) or s[pos] != "{":
        return None
    end = pos + 1
    while end < len(s) and s[end] not in "{}":
        end += 1
    if end < len(s) and s[end] == "}":
        return s[pos + 1:end], end + 1
    return None


def _class_and_style(s, pos):
    r = _ident(s, pos)
    if r is None:
        return None
    name, pos = r
    pos = _space(s, pos)
    if pos >= len(s) or s[pos] != "=":
        return None
    pos = _space(s, pos + 1)
    r = _css_styles(s, pos)
    if r is None:
        return None
    return (name, r[0]), r[1]


def parse_css_legend(text):
    """Parse the ``# Legend:`` block at the start of ``text``.

    Returns a list of (class, styles); raises ParseError if the header
    does not match.
    """
    s = text
    pos = _space(s, 0)
    if pos >= len(s) or s[pos] != "#":
        raise ParseError("expect #")
    pos = _space(s, pos + 1)
    if not s.startswith("Legend:", pos):
        raise ParseError("expect Legend:")
    pos = _space(s, pos + len("Legend:"))
    if pos >= len(s) or s[pos] not in "\r\n":
        raise ParseError("expect new line")
    pos += 1
    items = []
    r = _class_and_style(s, pos)
    if r is not None:
        items.append(r[0])
        pos = r[1]
        while pos < len(s) and s[pos] in "\r\n":
            r = _class_and_style(s, pos + 1)
            if r is None:
                break
            items.append(r[0])
            pos = r[1]
    return items


def line_parse(chars):
    """Locate the double-quoted strings in a line.

    ``chars`` is a sequence of characters.  Returns a list of
    (start, end) indices of the opening and closing quotes.  ``\\"`` inside
    a quoted string is an escaped quote.
    """
    n = len(chars)
    pos = 0
    result = []
    while True:
        p = pos
        while p < n and chars[p] != '"':
            p += 1
        if p >= n:
            break
        start = p
        p += 1
        while p < n:
            ch = chars[p]
            if ch == "\\" and p + 1 < n and chars[p + 1] == '"':
                p += 2
            elif ch != '"':
                p += 1
            else:
                break
        if p >= n:
            break
        end = p
        p += 1
        while p < n and chars[p] != '"':
            p += 1
        result.append((start, end))
        pos = p
    return result
