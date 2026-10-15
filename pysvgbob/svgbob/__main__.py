"""Command line interface, compatible with the ``svgbob`` 0.7.6 binary."""

import argparse
import os
import sys

from . import to_svg_with_settings, __version__
from .f32 import f32
from .settings import Settings


def _parse_number(kind, name, text):
    try:
        if kind is int:
            if not text.isdigit():
                raise ValueError("invalid digit found in string")
            return int(text)
        return f32(float(text))
    except ValueError as e:
        sys.stderr.write("Illegal value for argument %s: %s\n" % (name, e))
        sys.exit(1)


def _build(argv):
    parser = argparse.ArgumentParser(prog="svgbob build",
                                     description="Batch convert files to svg.")
    parser.add_argument("-i", "--input", default="*.bob",
                        help="set input file pattern like: *.bob or dir/*.bob")
    parser.add_argument("-o", "--outdir", default="",
                        help="set dir of svg files")
    args = parser.parse_args(argv)

    input_path = args.input
    ext = os.path.splitext(input_path)[1].lstrip(".") or "bob"
    input_dir = input_path if os.path.isdir(input_path) else os.path.dirname(input_path)
    input_dir = input_dir or "."
    if not os.path.isdir(input_dir):
        print("[Error]: No such dir name is %s !" % input_dir)
        return
    out_dir = args.outdir or input_dir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    for name in os.listdir(input_dir):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lstrip(".") == ext:
            out = os.path.join(out_dir, os.path.splitext(name)[0] + ".svg")
            print("%s => %s" % (path, out))
            try:
                with open(path, encoding="utf-8") as f:
                    bob = f.read()
                svg = to_svg_with_settings(bob, Settings())
                with open(out, "w", encoding="utf-8", newline="") as f:
                    f.write(svg)
            except (IOError, OSError) as e:
                print(e)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "build":
        _build(argv[1:])
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog="svgbob", description="SvgBobRus is an ascii to svg converter")
    parser.add_argument("-V", "--version", action="version",
                        version="svgbob %s" % __version__)
    parser.add_argument("--background",
                        help="backdrop background will be filled with this color (default: 'white')")
    parser.add_argument("-s", dest="inline", action="store_true",
                        help="parse an inline string")
    parser.add_argument("input", nargs="?",
                        help="svgbob text file or inline string to parse [default: STDIN]")
    parser.add_argument("-o", "--output",
                        help="where to write svg output [default: STDOUT]")
    parser.add_argument("--fill-color",
                        help="solid shapes will be filled with this color (default: 'black')")
    parser.add_argument("--font-family",
                        help="text will be rendered with this font (default: 'arial')")
    parser.add_argument("--font-size",
                        help="text will be rendered with this font size (default: 14)")
    parser.add_argument("--stroke-width",
                        help="stroke width for all lines (default: 2)")
    parser.add_argument("--stroke-color",
                        help="stroke color for all lines (default: 'black')")
    parser.add_argument("--scale",
                        help="scale the entire svg (dimensions, font size, stroke width) by this factor (default: 1)")
    args = parser.parse_args(argv)

    if args.inline:
        if args.input is None:
            parser.error("-s needs an inline string")
        bob = args.input.replace("\\n", "\n")
    elif args.input is not None:
        try:
            with open(args.input, encoding="utf-8", newline="") as f:
                bob = f.read()
        except (IOError, OSError) as e:
            sys.stderr.write("Failed to open input file %s: %s\n" % (args.input, e))
            sys.exit(1)
    else:
        bob = sys.stdin.buffer.read().decode("utf-8")

    settings = Settings()
    if args.background is not None:
        settings.background = args.background
    if args.fill_color is not None:
        settings.fill_color = args.fill_color
    if args.font_family is not None:
        settings.font_family = args.font_family
    if args.font_size is not None:
        settings.font_size = _parse_number(int, "font-size", args.font_size)
    if args.stroke_width is not None:
        settings.stroke_width = _parse_number(float, "stroke-width", args.stroke_width)
    if args.stroke_color is not None:
        settings.stroke_color = args.stroke_color
    if args.scale is not None:
        settings.scale = settings.scale * _parse_number(float, "scale", args.scale)

    svg = to_svg_with_settings(bob, settings)

    if args.output is not None:
        try:
            with open(args.output, "w", encoding="utf-8", newline="") as f:
                f.write(svg)
        except (IOError, OSError) as e:
            sys.stderr.write("Failed to write to output file %s: %s\n" % (args.output, e))
            sys.exit(2)
    else:
        sys.stdout.buffer.write((svg + "\n").encode("utf-8"))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
