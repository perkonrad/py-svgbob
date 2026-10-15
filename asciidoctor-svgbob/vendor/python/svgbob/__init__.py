"""Pure Python port of svgbob 0.7.6: convert ascii diagrams into svg.

>>> import svgbob
>>> svg = svgbob.to_svg("+--+\\n|ab|\\n+--+\\n")

The output matches the Rust ``svgbob`` 0.7.6 crate.
"""

from .settings import Settings
from .buffer import CellBuffer

__version__ = "0.7.6"

__all__ = ["Settings", "CellBuffer", "to_svg", "to_svg_string_pretty",
           "to_svg_string_compressed", "to_svg_with_settings",
           "to_svg_with_override_size"]


def _render(node, pretty=True):
    out = []
    if pretty:
        node.render(out)
    else:
        node.render_compressed(out)
    return "".join(out)


def to_svg(ascii):
    """Convert ascii art to an indented svg string with the default settings."""
    return to_svg_string_pretty(ascii)


def to_svg_string_pretty(ascii):
    node, _w, _h = CellBuffer.from_str(ascii).get_node_with_size(Settings())
    return _render(node)


def to_svg_string_compressed(ascii):
    """Like :func:`to_svg` but without line breaks and indentation."""
    node, _w, _h = CellBuffer.from_str(ascii).get_node_with_size(Settings())
    return _render(node, pretty=False)


def to_svg_with_settings(ascii, settings):
    node, _w, _h = CellBuffer.from_str(ascii).get_node_with_size(settings)
    return _render(node)


def to_svg_with_override_size(ascii, settings, w, h):
    node = CellBuffer.from_str(ascii).get_node_override_size(settings, w, h)
    return _render(node)
