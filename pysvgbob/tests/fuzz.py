#!/usr/bin/env python3
"""Differential fuzzing of the Python port against the svgbob binary.

usage: tests/fuzz.py [count] [seed]

Random ascii art (dense line-drawing characters, boxes, circles, quoted
text and unicode box characters) is converted by both implementations and
the outputs compared.  Failing inputs are written to tests/fuzz_failures/.
"""

import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import svgbob  # noqa: E402

DRAW = "-|+/\\_.,'`()<>^vV*oO#~!:=X"
TEXT = "abcxyz{}0123 "
UNICODE = "─│┌┐└┘├┤┬┴┼╭╮╰╯═║╔╗╚╝▶◀▲▼●○◆┄╎"
CIRCLES = [
    [" ,-.", "(   )", " `-'"],
    [" .--.", "(    )", " `--'"],
    ["   _", " .' '.", "(     )", " `._.'"],
    ["   ___", " ,'   `.", "/       \\", "\\       /", " `.___.'"],
    ["  ()", " (_)"],
]


def random_art(rng):
    h = rng.randint(1, 9)
    w = rng.randint(1, 24)
    grid = [[" "] * w for _ in range(h)]
    style = rng.random()
    for y in range(h):
        for x in range(w):
            r = rng.random()
            if r < 0.35:
                grid[y][x] = rng.choice(DRAW)
            elif r < 0.42:
                grid[y][x] = rng.choice(TEXT)
            elif r < 0.45 and style < 0.3:
                grid[y][x] = rng.choice(UNICODE)
    # sprinkle boxes
    for _ in range(rng.randint(0, 3)):
        bw, bh = rng.randint(2, 10), rng.randint(2, 5)
        x0, y0 = rng.randint(0, max(0, w - 1)), rng.randint(0, max(0, h - 1))
        corner = rng.choice(["+", ".", "'", "+"])
        horiz = rng.choice(["-", "-", "~", "="])
        vert = rng.choice(["|", "|", "!", ":"])
        for x in range(x0, x0 + bw):
            for y in (y0, y0 + bh):
                if y < h and x < w:
                    grid[y][x] = horiz
        for y in range(y0, y0 + bh + 1):
            for x in (x0, x0 + bw):
                if y < h and x < w:
                    grid[y][x] = vert
        for (x, y) in ((x0, y0), (x0 + bw, y0), (x0, y0 + bh), (x0 + bw, y0 + bh)):
            if y < h and x < w:
                grid[y][x] = corner if corner != "'" or y != y0 else "."
    # sprinkle circles
    if rng.random() < 0.3:
        art = rng.choice(CIRCLES)
        x0, y0 = rng.randint(0, w), rng.randint(0, h)
        for dy, row in enumerate(art):
            for dx, ch in enumerate(row):
                y, x = y0 + dy, x0 + dx
                while y >= len(grid):
                    grid.append([" "] * w)
                while x >= len(grid[y]):
                    grid[y].append(" ")
                if ch != " ":
                    grid[y][x] = ch
    lines = ["".join(row).rstrip() for row in grid]
    # sometimes a quoted string
    if rng.random() < 0.15 and lines:
        i = rng.randrange(len(lines))
        lines[i] = lines[i] + ' "q|-+"'
    text = "\n".join(lines) + "\n"
    if rng.random() < 0.05:
        text += "# Legend:\nq = {fill:red}\n"
    return text


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    fail_dir = os.path.join(HERE, "fuzz_failures")
    failures = 0
    skipped = 0
    for n in range(count):
        art = random_art(rng)
        ref = subprocess.run(["svgbob"], input=art.encode("utf-8"),
                             capture_output=True)
        if ref.returncode != 0:
            skipped += 1
            continue  # the binary panicked; nothing to compare against
        try:
            got = svgbob.to_svg(art) + "\n"
        except Exception as e:  # noqa: BLE001
            got = "EXCEPTION %r" % (e,)
        if got != ref.stdout.decode("utf-8"):
            failures += 1
            os.makedirs(fail_dir, exist_ok=True)
            with open(os.path.join(fail_dir, "fail_%d_%d.bob" % (seed, n)),
                      "w", encoding="utf-8") as f:
                f.write(art)
    print("%d cases, %d failures, %d skipped (binary crashed) (seed %d)"
          % (count, failures, skipped, seed))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
