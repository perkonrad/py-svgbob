require_relative 'lib/asciidoctor/svgbob/version'

Gem::Specification.new do |s|
  s.name        = 'asciidoctor-svgbob'
  s.version     = Asciidoctor::Svgbob::VERSION
  s.summary     = 'Asciidoctor extension that renders svgbob ascii diagrams to SVG'
  s.description = 'An [svgbob] block and svgbob:: block macro for Asciidoctor (HTML and PDF). ' \
                  'Bundles a pure Python port of svgbob 0.7.6, or runs any svgbob command.'
  s.authors     = ['Per Konradsson']
  s.license     = 'Apache-2.0'
  s.files       = Dir['lib/**/*.rb', 'vendor/python/svgbob/*.py', 'README.md', 'LICENSE']
  s.require_paths = ['lib']
  s.required_ruby_version = '>= 2.7'
  s.add_runtime_dependency 'asciidoctor', '~> 2.0'
end
