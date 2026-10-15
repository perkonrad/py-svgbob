# asciidoctor-svgbob

An Asciidoctor extension that renders [svgbob](https://github.com/ivanceras/svgbob)
ascii diagrams to SVG, for the HTML and PDF converters.

It bundles the pure Python port of svgbob 0.7.6 (`../pysvgbob`, in
`vendor/python`), so the only other thing it needs is `python3`. It can run
the Rust `svgbob` binary instead; both give the same SVG.

## Usage

```sh
asciidoctor     -r asciidoctor-svgbob doc.adoc     # installed gem
asciidoctor-pdf -r asciidoctor-svgbob doc.adoc
asciidoctor     -r ./lib/asciidoctor-svgbob.rb doc.adoc   # from this directory
```

```asciidoc
[[fig-flow]]
[%unbreakable]
.The flow
[svgbob,fig-flow,svg]
....
+-------+     +------+
| input |---->| core |---> "result"
+-------+     +------+
....

svgbob::diagrams/ring.bob[]
```

- **Block:** `[svgbob, target, format]` on a literal, listing, open or
  paragraph block. `target` is the image name without `.svg`. Without a
  target, the name comes from a checksum of the diagram. `format` is `svg`
  (the default) or `txt`, which keeps the diagram as a literal block.
- **Block macro:** `svgbob::file.bob[format, target=name]` reads the diagram
  from a file relative to the document. The image is named after the file.
- **Block features:** the id, title (with its "Figure N." caption), roles and
  options such as `%unbreakable` or `opts=inline` carry over to the image
  block.

The syntax is the same as asciidoctor-diagram's `svgbob` block, so existing
documents work unchanged.

## Attributes

Set them on a block, or for the whole document with an `svgbob-` prefix
(`:svgbob-stroke-width: 1.5`). A block attribute wins over the document one.

| attribute          | meaning (svgbob default)                          |
|--------------------|---------------------------------------------------|
| `background`       | backdrop colour (`white`)                         |
| `fill-color`       | colour of solid shapes (`black`)                  |
| `font-family`      | text font (`Iosevka Fixed, monospace`)            |
| `font-size`        | text size in px (`14`)                            |
| `stroke-color`     | line and text colour (`black`)                    |
| `stroke-width`     | line width (`2`)                                  |
| `scale`            | scale factor of the drawing (`1`)                 |
| `fit-text`         | `off` turns off widening for labels (on)          |

Document-only attributes:

| attribute          | meaning                                            |
|--------------------|----------------------------------------------------|
| `svgbob-command`   | the svgbob command, e.g. `svgbob` for the Rust binary (default: the bundled Python port) |
| `svgbob-python`    | the Python interpreter for the bundled port (`python3`) |
| `svgbob-cachedir`  | where checksums are kept (`<outdir>/.asciidoctor/svgbob`) |
| `svgbob-nocache`   | always regenerate (also `%nocache` on a block)     |
| `svgbob-on-error`  | `abort` raises; the default logs an error and shows the diagram as text |
| `imagesoutdir`     | where the SVGs are written (default `<outdir>/<imagesdir>`) |

## Labels at the right edge

svgbob sizes the canvas from the line art only, so a label (quoted text)
that runs past the rightmost line, or sits below the lowest one, is clipped.
The extension widens the SVG, its backdrop and the HTML `<img>` size to fit:

- **Width:** 8.6 px per character at a 14 px font, plus 16 px.
- **Height:** when descenders would be cut off, 20 px below the lowest
  baseline.

`fit-text=off` keeps svgbob's own size. A diagram whose labels all fit is
left unchanged, byte for byte.

## Caching

Each SVG is regenerated only when the diagram, its options, the command or
the extension version change. A checksum is kept in the cache directory.
That makes a PDF run after an HTML run cheap.

## Paths

Images go to `imagesoutdir` if set, otherwise to `outdir/imagesdir`.

- **HTML:** the image block links to the SVG relative to the output.
- **data-uri, `opts=inline` and PDF:** the SVG is read relative to the
  document. If it is not under `docdir/imagesdir`, an absolute path is
  used. Reading such a path needs the CLI's default unsafe mode.

## With asciidoctor-diagram

Both extensions register the `svgbob` block, and the one loaded last handles
it. `-r asciidoctor-diagram -r asciidoctor-svgbob` keeps asciidoctor-diagram
for the other diagram types and uses this extension for svgbob.

## Development

```sh
make vendor   # copy ../pysvgbob/svgbob into vendor/python
make test     # ruby -Ilib test/test_svgbob.rb (compares with `svgbob` if on PATH)
make gem      # build asciidoctor-svgbob-<version>.gem
```

Install with `gem install asciidoctor-svgbob-0.1.0.gem`. On systems that
default to `--user-install`, `--install-dir` needs `--no-user-install`.
