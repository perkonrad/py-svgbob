"""A tiny element tree that renders like sauron 0.61 does for svgbob.

* Attributes with the same name are merged into the position of the first
  one; their values are joined with a space (only ``class`` repeats here).
  An attribute whose merged value is empty renders as nothing, but the
  separating space is still written (hence ``<text x="1" y="2" >``).
* An element whose only child is a text node is rendered on one line.
* Other children go on their own line, indented by two spaces per level.
* Text content is written as is; callers escape it beforehand.
"""


class Text(object):
    __slots__ = ("text",)

    def __init__(self, text):
        self.text = text


class Element(object):
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = list(attrs or [])
        self.children = list(children or [])

    def with_attributes(self, attrs):
        self.attrs.extend(attrs)
        return self

    def with_children(self, children):
        self.children.extend(children)
        return self

    def _merged_attrs(self):
        order = []
        values = {}
        for name, value in self.attrs:
            if name not in values:
                order.append(name)
                values[name] = []
            if isinstance(value, (list, tuple)):
                values[name].extend(value)
            else:
                values[name].append(value)
        return [(name, " ".join(v for v in values[name] if v != "")) for name in order]

    def render(self, out, indent=0, pretty=True):
        out.append("<")
        out.append(self.tag)
        for name, value in self._merged_attrs():
            out.append(" ")
            if value != "":
                out.append('%s="%s"' % (name, value))
        out.append(">")
        children = self.children
        lone_text = len(children) == 1 and isinstance(children[0], Text)
        if lone_text or not pretty:
            for child in children:
                if isinstance(child, Text):
                    out.append(child.text)
                else:
                    child.render(out, indent + 1, pretty)
        else:
            for child in children:
                out.append("\n" + "  " * (indent + 1))
                if isinstance(child, Text):
                    out.append(child.text)
                else:
                    child.render(out, indent + 1)
            if children:
                out.append("\n" + "  " * indent)
        out.append("</%s>" % self.tag)

    def render_compressed(self, out):
        self.render(out, pretty=False)

    def to_string(self):
        out = []
        self.render(out)
        return "".join(out)


def element(tag, attrs=None, children=None):
    return Element(tag, attrs, children)
