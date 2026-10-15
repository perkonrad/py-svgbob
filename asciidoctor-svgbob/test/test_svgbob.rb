# Tests for asciidoctor-svgbob. No test framework needed:
#
#   ruby -Ilib test/test_svgbob.rb
#
# The tests that compare with the Rust svgbob binary are skipped when it is
# not on PATH; the PDF test is skipped without asciidoctor-pdf.

require 'asciidoctor'
require 'asciidoctor-svgbob'
require 'fileutils'
require 'tmpdir'

FIXTURES = File.expand_path('fixtures', __dir__)
$failures = 0
$count = 0

def check(name, cond, detail = nil)
  $count += 1
  if cond
    puts "ok   #{name}"
  else
    $failures += 1
    puts "FAIL #{name}#{detail ? ': ' + detail.to_s : ''}"
  end
end

def which(cmd)
  ENV['PATH'].split(File::PATH_SEPARATOR).any? {|d| File.executable?(File.join(d, cmd)) }
end

def convert(input, dir, **opts)
  attrs = opts.delete(:attributes) || {}
  Asciidoctor.convert input, safe: :unsafe, to_file: File.join(dir, 'out.html'),
                             mkdirs: true, base_dir: dir, attributes: attrs, **opts
  File.read File.join(dir, 'out.html')
end

BOX = <<~'EOS'
  [[fig-box]]
  [%unbreakable]
  .A box
  [svgbob,fig-box,svg]
  ....
  +------+
  | box  |--->
  +------+
  ....
EOS

Dir.mktmpdir do |dir|
  # block -> image block with caption, id and size
  html = convert BOX, dir
  svg_file = File.join(dir, 'fig-box.svg')
  check 'block writes the svg', File.exist?(svg_file)
  check 'image block keeps the id', html.include?('<div id="fig-box" class="imageblock">')
  check 'figure caption', html.include?('Figure 1. A box')
  svg = File.read svg_file
  w, h = Asciidoctor::Svgbob::Renderer.size svg
  check 'img gets the svg size', html.include?(%(width="#{w.to_i}" height="#{h.to_i}"))

  # output equals the Rust binary for diagrams without overflowing text
  if which 'svgbob'
    art = "+------+\n| box  |--->\n+------+\n"
    rust = IO.popen(%w(svgbob), 'r+') {|io| io.write art; io.close_write; io.read }.rstrip
    check 'same svg as the Rust binary', svg == rust
  end

  # cache: a second run does not regenerate
  mtime = File.mtime svg_file
  sleep 1.1
  convert BOX, dir
  check 'cached svg reused', File.mtime(svg_file) == mtime
  convert BOX.sub('box ', 'BOX '), dir
  check 'changed diagram regenerated', File.mtime(svg_file) != mtime
end

Dir.mktmpdir do |dir|
  # labels past the right edge are fitted, and fit-text can be turned off
  art = %([svgbob,label,svg]\n....\n+--+\n|  |--> "a long label past the edge"\n+--+\n....\n)
  convert art, dir
  w_fit, = Asciidoctor::Svgbob::Renderer.size File.read(File.join(dir, 'label.svg'))
  convert art, dir, attributes: { 'svgbob-fit-text' => 'off' }
  w_raw, = Asciidoctor::Svgbob::Renderer.size File.read(File.join(dir, 'label.svg'))
  check 'fit-text widens', w_fit > w_raw, [w_fit, w_raw]
  check 'fit-text covers the label', w_fit >= 8 * 8 + 2 + 8.6 * 26, w_fit
end

Dir.mktmpdir do |dir|
  # block macro, txt format, auto name, options, imagesdir
  FileUtils.cp File.join(FIXTURES, 'diagram.bob'), dir
  input = <<~'EOS'
    :imagesdir: img

    svgbob::diagram.bob[]

    [svgbob,scaled,scale=2,stroke-color=blue]
    ....
    o--->
    ....

    [svgbob,plain,txt]
    ....
    +--+
    ....

    [svgbob]
    ....
    -->
    ....
  EOS
  html = convert input, dir
  check 'macro: image named after the file', File.exist?(File.join(dir, 'img', 'diagram.svg'))
  check 'imagesdir in the src', html.include?('src="img/diagram.svg"')
  scaled = File.read File.join(dir, 'img', 'scaled.svg')
  check 'scale option', scaled.include?('width="96"'), scaled[/<svg[^>]*>/]
  check 'stroke-color option', scaled.include?('stroke: blue;')
  check 'txt format is a literal block', html.include?(%(<div class="literalblock">)) && html.include?('+--+')
  auto = Dir[File.join(dir, 'img', 'svgbob-*.svg')]
  check 'block without target gets a checksum name', auto.size == 1, auto
end

Dir.mktmpdir do |dir|
  # failures are logged and the source is kept
  logger = Asciidoctor::MemoryLogger.new
  old = Asciidoctor::LoggerManager.logger
  Asciidoctor::LoggerManager.logger = logger
  begin
    html = convert %([svgbob,bad,svg]\n....\n+--+\n....\n), dir,
                   attributes: { 'svgbob-command' => 'false' }
  ensure
    Asciidoctor::LoggerManager.logger = old
  end
  msg = logger.messages.map {|m| m[:message].respond_to?(:text) ? m[:message].text : m[:message].to_s }.join
  check 'failure is logged', msg.include?('svgbob: Failed to generate image')
  check 'failure keeps the source', html.include?('+--+')
end

if which 'svgbob'
  Dir.mktmpdir do |dir|
    # the Rust binary as the renderer gives the same svg
    convert BOX, dir, attributes: { 'svgbob-command' => 'svgbob', 'svgbob-fit-text' => 'off' }
    rust = File.read File.join(dir, 'fig-box.svg')
    FileUtils.rm_rf Dir[File.join(dir, '*')] + [File.join(dir, '.asciidoctor')]
    convert BOX, dir, attributes: { 'svgbob-fit-text' => 'off' }
    check 'python port and Rust binary agree', rust == File.read(File.join(dir, 'fig-box.svg'))
  end
end

begin
  require 'asciidoctor/pdf'
  Dir.mktmpdir do |dir|
    # PDF: images written outside the document directory are found
    src = File.join(dir, 'src')
    FileUtils.mkdir_p src
    File.write File.join(src, 'doc.adoc'), %(= PDF\n\n#{BOX})
    logger = Asciidoctor::MemoryLogger.new
    old = Asciidoctor::LoggerManager.logger
    Asciidoctor::LoggerManager.logger = logger
    begin
      Asciidoctor.convert_file File.join(src, 'doc.adoc'), backend: 'pdf', safe: :unsafe,
                               to_file: File.join(dir, 'out', 'doc.pdf'), mkdirs: true
    ensure
      Asciidoctor::LoggerManager.logger = old
    end
    check 'pdf written', File.exist?(File.join(dir, 'out', 'doc.pdf'))
    check 'pdf without warnings', logger.messages.empty?, logger.messages.map {|m| m[:message] }
  end
rescue LoadError
  puts 'skip pdf (asciidoctor-pdf not installed)'
end

puts "#{$count} checks, #{$failures} failures"
exit($failures.zero? ? 0 : 1)
