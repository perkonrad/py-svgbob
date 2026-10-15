"""Unit tests, mostly ported from the Rust crate, plus a differential test
against the reference ``svgbob`` binary when it is on PATH.

run: python3 -m unittest discover -s tests
"""

import glob
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import svgbob  # noqa: E402
from svgbob import Settings  # noqa: E402
from svgbob.buffer import CellBuffer, contacts_from_span  # noqa: E402
from svgbob.f32 import fmt  # noqa: E402
from svgbob.fragment import Arc, Line, Rect  # noqa: E402
from svgbob.geom import Cell, CellGrid, Point, is_collinear  # noqa: E402
from svgbob.parser import (ParseError, line_parse, parse_css_legend,  # noqa: E402
                           parse_css_tag)

G = CellGrid


class SimpleShapes(unittest.TestCase):
    """crates/svgbob/tests/simple_shapes.rs"""

    def check(self, bob, expected):
        self.assertEqual(expected,
                         svgbob.to_svg_with_settings(bob, Settings.for_debug()))

    def test_rect1(self):
        self.check("""
    +----------+
    |          |
    +----------+
    """, """<svg xmlns="http://www.w3.org/2000/svg" width="136" height="80" class="svgbob">
  <rect x="36" y="24" width="88" height="32" class="solid nofill" rx="0"></rect>
</svg>""")

    def test_escaped_shape(self):
        self.check('''
    "+----------+"
    "|          |"
    "+----------+"
    ''', """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="32" class="svgbob">
  <text x="34" y="28" >+----------+</text>
  <text x="34" y="44" >|          |</text>
  <text x="34" y="60" >+----------+</text>
</svg>""")

    def test_rounded_rect(self):
        self.check("""
    .----------.
    |          |
    '----------'
    """, """<svg xmlns="http://www.w3.org/2000/svg" width="136" height="80" class="svgbob">
  <rect x="36" y="24" width="88" height="32" class="solid nofill" rx="4"></rect>
</svg>""")

    def test_just_v(self):
        self.check("""
        V
    """, """<svg xmlns="http://www.w3.org/2000/svg" width="80" height="48" class="svgbob">
  <text x="66" y="28" >V</text>
</svg>""")

    def test_arrow_down(self):
        self.check("""
        |
        V
    """, """<svg xmlns="http://www.w3.org/2000/svg" width="80" height="64" class="svgbob">
  <line x1="68" y1="16" x2="68" y2="36" class="solid"></line>
  <polygon points="64,36 72,36 68,48" class="filled"></polygon>
</svg>""")


class Parser(unittest.TestCase):
    """util.rs parser tests"""

    def test_escaped_string(self):
        raw = r'The "qu/i/ck" brown "fox\"s" jumps over the lazy "do|g"'
        locs = line_parse(list(raw))
        self.assertEqual([raw[s:e + 1] for s, e in locs],
                         ['"qu/i/ck"', r'"fox\"s"', '"do|g"'])

    def test_css_legend(self):
        self.assertEqual(
            parse_css_legend("# Legend: \na = {fill:blue; stroke:red;}\n"
                             "b = {fill:red; stroke:black;}"),
            [("a", "fill:blue; stroke:red;"), ("b", "fill:red; stroke:black;")])
        self.assertEqual(
            parse_css_legend("# Legend:\nbig_circle = {fill:blue;}\nred = {stroke:red;}\n"),
            [("big_circle", "fill:blue;"), ("red", "stroke:red;")])
        with self.assertRaises(ParseError):
            parse_css_legend("# Legend1: \na = {fill:blue;}")

    def test_css_styles_with_new_line(self):
        self.assertEqual(parse_css_legend("# Legend:\na = {fill:blue;\nstroke:red;}"),
                         [("a", "fill:blue;\nstroke:red;")])

    def test_tag_classes(self):
        self.assertEqual(parse_css_tag("{blue_circle}"), ["blue_circle"])
        self.assertEqual(parse_css_tag("{blue_circle,red_dot}"),
                         ["blue_circle", "red_dot"])
        for bad in ("{blue_circle", "{blue_*circle}"):
            with self.assertRaises(ParseError):
                parse_css_tag(bad)


class Buffers(unittest.TestCase):
    """cell_buffer.rs / span tests"""

    def test_escape_line(self):
        raw = r'The "qu/i/ck" brown "fox\"s" jumps over the lazy "do|g"'
        escaped, unescaped = CellBuffer.escape_line(0, raw)
        self.assertEqual(escaped, [(Cell(4, 0), "qu/i/ck"),
                                   (Cell(20, 0), r'fox\"s'),
                                   (Cell(49, 0), "do|g")])
        self.assertEqual(unescaped,
                         "The           brown          jumps over the lazy       ")

    def test_escape_cjk(self):
        escaped, unescaped = CellBuffer.escape_line(
            0, 'This is some CJK "一" and was escaped')
        self.assertEqual(escaped, [(Cell(17, 0), "一")])
        self.assertEqual(unescaped, "This is some CJK      and was escaped")

    def test_simple_adjacents(self):
        art = """
..     ._.
''    (   )
       `-'

.--------.
|________|
    """
        self.assertEqual(len(CellBuffer.from_str(art).spans()), 3)

    def test_one_big(self):
        art = """

       .---.
      /-o-/--
   .-/ / /->
  ( *  \\/
   '-.  \\
      \\ /
       '
    """
        self.assertEqual(len(CellBuffer.from_str(art).spans()), 1)

    def test_1span_1group(self):
        art = """
+--------+
|        |
+--------+
    """
        spans = CellBuffer.from_str(art).spans()
        self.assertEqual(len(spans), 1)
        groups = contacts_from_span(spans[0].localize())
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].endorse_rect(),
                         Rect(Point(0.5, 1.0), Point(9.5, 5.0), False, False))


class Geometry(unittest.TestCase):

    def test_arc_centers(self):
        self.assertEqual(G.o(), Arc(G.e(), G.y(), 1.0).center())
        self.assertEqual(G.a(), Arc(G.k(), G.e(), 1.0).center())
        self.assertEqual(G.e(), Arc(G.a(), G.o(), 1.0).center())
        self.assertEqual(G.t(), Arc(G.o(), G.r(), 0.5).center())
        self.assertEqual(G.p(), Arc(G.r(), G.k(), 0.5).center())
        self.assertTrue(Arc(G.o(), G.r(), 0.5).is_aabb_right_angle_arc())

    def test_line_angle(self):
        self.assertEqual(Line(G.c(), G.m()).line_angle(), 270.0)
        self.assertEqual(Line(G.m(), G.o()).line_angle(), 0.0)
        self.assertEqual(Line(G.a(), G.y()).line_angle(), 296.565)
        self.assertEqual(Line(G.u(), G.e()).line_angle(), 243.435)
        self.assertEqual(Line(G.e(), G.u()).line_angle(), 243.435)

    def test_collinear(self):
        self.assertTrue(is_collinear(G.a(), G.b(), G.c()))
        self.assertFalse(is_collinear(G.f(), G.c(), G.e()))

    def test_merge(self):
        self.assertEqual(Line(G.k(), G.m()).merge(Line(G.m(), G.o())),
                         Line(G.k(), G.o()))
        self.assertIsNone(Line(G.k(), G.l()).merge(Line(G.n(), G.o())))
        self.assertIsNone(Line(G.k(), G.o()).merge(Line(G.o(), G.j())))

    def test_fmt(self):
        self.assertEqual(fmt(8.0), "8")
        self.assertEqual(fmt(4.5), "4.5")
        self.assertEqual(fmt(1.0 / 3.0), "0.33333334")
        self.assertEqual(fmt(299.203125), "299.20313")
        self.assertEqual(fmt(-0.0), "-0")


@unittest.skipUnless(shutil.which("svgbob"), "reference svgbob binary not found")
class AgainstBinary(unittest.TestCase):
    """The output must be byte-identical to the Rust svgbob binary."""

    def test_files(self):
        files = sorted(glob.glob(os.path.join(HERE, "cases", "*.bob")))
        rust_data = os.path.join(HERE, "..", "..", "svgbob", "crates", "svgbob",
                                 "test_data")
        files += sorted(glob.glob(os.path.join(rust_data, "*.bob")))
        for path in files:
            with self.subTest(path=os.path.basename(path)):
                ref = subprocess.run(["svgbob", path], capture_output=True,
                                     check=True).stdout.decode("utf-8")
                with open(path, encoding="utf-8", newline="") as f:
                    got = svgbob.to_svg(f.read()) + "\n"
                self.assertTrue(ref == got, "output differs for %s" % path)


if __name__ == "__main__":
    unittest.main()
