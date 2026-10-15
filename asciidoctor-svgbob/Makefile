# asciidoctor-svgbob
#
#   make vendor   copy the Python port (../pysvgbob/svgbob) into vendor/python
#   make test     run the tests (needs asciidoctor and asciidoctor-pdf)
#   make gem      build asciidoctor-svgbob-<version>.gem

PYSVGBOB ?= ../pysvgbob/svgbob

.PHONY: vendor test gem
vendor:
	rm -rf vendor/python/svgbob
	mkdir -p vendor/python/svgbob
	cp $(PYSVGBOB)/*.py vendor/python/svgbob/

test:
	ruby -Ilib test/test_svgbob.rb

gem: vendor
	gem build asciidoctor-svgbob.gemspec
