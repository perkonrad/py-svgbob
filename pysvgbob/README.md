# svgbob (Python port)

A pure Python port of [svgbob](https://github.com/ivanceras/svgbob) 0.7.6,
which turns ascii diagrams into SVG. It uses only the standard library and
needs Python 3.9 or newer.

The output is byte-identical to the Rust `svgbob` 0.7.6 binary for every
input tested so far:

- all 8 files in `crates/svgbob/test_data`
- the edge cases in `tests/cases`
- 7,000 random diagrams from the differential fuzzer
- the CLI options, including fractional `--scale` values

## Usage

Command line (same options as the Rust binary):

```sh
python3 -m svgbob diagram.bob -o diagram.svg
python3 -m svgbob -s '+--+\n|ab|\n+--+'
cat diagram.bob | python3 -m svgbob --scale 2 --stroke-width 1.5 > out.svg
python3 -m svgbob build -i 'docs/*.bob' -o out/
```

When installed (`pip install .`) the command is also available as `svgbob-py`.

Library:

```python
import svgbob

svg = svgbob.to_svg(text)                       # default settings
settings = svgbob.Settings(stroke_width=1.5, background="#eee")
svg = svgbob.to_svg_with_settings(text, settings)
svg = svgbob.to_svg_string_compressed(text)     # no indentation
```

`Settings.for_debug()` leaves out the style, marker definitions and backdrop,
like the Rust crate.

## Layout

| module            | Rust source                                   |
|-------------------|-----------------------------------------------|
| `f32.py`          | f32 rounding and `Display` formatting         |
| `geom.py`         | `point.rs`, `cell.rs`, `cell_grid.rs`, parry2d helpers |
| `fragment.py`     | `fragment/*.rs`, `direction.rs`               |
| `property.py`     | `property_buffer/property.rs`                 |
| `ascii_map.py`    | `map/ascii_map.rs`                            |
| `unicode_map.py`  | `map/unicode_map.rs`                          |
| `circle_map.py`   | `map/circle_map.rs`                           |
| `buffer.py`       | `cell_buffer*.rs`, `span.rs`, `contacts.rs`, `endorse.rs`, `fragment_buffer*.rs`, `fragment_tree.rs`, `string_buffer.rs` |
| `parser.py`       | the pom parsers in `util.rs`                  |
| `svg.py`          | sauron's element rendering                    |
| `__main__.py`     | `svgbob_cli`                                  |

## How it stays identical

- **f32 arithmetic.** svgbob computes in single precision, and some
  decisions compare floats exactly (for example, whether a rounded corner's
  arc centre lines up with the corner). Every stored result is rounded to
  f32. Numbers are printed like Rust's `Display` for `f32`: the shortest
  digits that round-trip, with ties rounded up.
- **Sorting.** Some fragment orderings in the Rust code are not transitive
  across fragment types. Lists of up to 20 items are therefore sorted with the
  same insertion sort Rust's `slice::sort` uses.
- **Parser quirks.** The legend and `{tag}` parsers copy pom's behaviour.
  For example, a legend line that starts with a space ends the legend.
- **Text width.** Quoted strings use the unicode-width 0.1.14 rules: control
  characters, including the `\0` padding after wide characters, count as 1;
  emoji sequences with U+FE0F count as 2; lam+alef counts as 1.

## Known limits

- Character widths come from Python's `unicodedata` (Unicode 13 on Python
  3.9), not the tables in unicode-width 0.1.14. Characters added to Unicode
  after version 13 may get a different width.
- The emoji-presentation rule (a character followed by U+FE0F) uses an
  approximate list of base characters.
- Lists of more than 20 fragments are sorted with Python's sort, not
  Rust's. This only matters if the inconsistent ordering above shows up in
  such a list, and no test has hit it.
- It is slower than Rust: about 5 s for the 2,000-line `long.bob` and well
  under a second for typical diagrams.

## Tests

```sh
python3 -m unittest discover -s tests   # unit tests; diffs against `svgbob` if on PATH
tests/compare.sh [files.bob...]          # byte-compare with the svgbob binary
python3 tests/fuzz.py 1000 1             # random differential fuzzing (count, seed)
```
