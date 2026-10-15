require 'asciidoctor'
require 'asciidoctor/extensions'
require_relative 'svgbob/version'
require_relative 'svgbob/renderer'
require_relative 'svgbob/extension'

Asciidoctor::Extensions.register do
  block Asciidoctor::Svgbob::BlockProcessor
  block_macro Asciidoctor::Svgbob::BlockMacroProcessor
end
