# py-svgbob

A pure Python port of [svgbob](https://github.com/ivanceras/svgbob) 0.7.6,
and an Asciidoctor extension that uses it to render svgbob diagrams in
HTML and PDF documents. The SVG is byte for byte the same as the Rust
`svgbob` 0.7.6 binary.

| Directory             | What it is                                              |
|-----------------------|---------------------------------------------------------|
| `pysvgbob/`           | The Python port: library and `python3 -m svgbob` CLI    |
| `asciidoctor-svgbob/` | The Asciidoctor extension, with a copy of the port in `vendor/python` |

Each directory has its own README.

## Using the extension

The extension needs only Ruby, Asciidoctor and `python3`; nothing has to be
installed:

```sh
asciidoctor     -r ./asciidoctor-svgbob/lib/asciidoctor-svgbob.rb doc.adoc
asciidoctor-pdf -r ./asciidoctor-svgbob/lib/asciidoctor-svgbob.rb doc.adoc
```

## Development

```sh
cd pysvgbob && python3 -m unittest discover -s tests   # the port
make -C asciidoctor-svgbob vendor                      # copy the port into the extension
make -C asciidoctor-svgbob test                        # the extension
make -C asciidoctor-svgbob gem                         # build the gem
```

After changing `pysvgbob/svgbob`, run `make vendor` so that the extension
carries the same code. `pysvgbob/tests/compare.sh` checks the port against
the Rust `svgbob` binary on the PATH. Without arguments it reads the
crate's `test_data` from a svgbob checkout next to this repository's
`pysvgbob/` directory (`../svgbob`), so pass the `.bob` files explicitly
otherwise.

## License

Apache-2.0, the same as svgbob. See `LICENSE`.
