require 'open3'
require 'shellwords'

module Asciidoctor
  module Svgbob
    # Runs svgbob on a diagram and returns the SVG.
    #
    # The default command is the pure Python port bundled in vendor/python,
    # run in isolated mode (-I) so that nothing in the current directory or
    # the environment can shadow it. Any svgbob-compatible command line works
    # instead, e.g. the Rust binary: both take the same flags and read the
    # diagram on stdin.
    module Renderer
      VENDOR_DIR = ::File.expand_path('../../../vendor/python', __dir__)

      # svgbob command line options, by attribute name
      OPTIONS = %w(background fill-color font-family font-size stroke-color stroke-width scale).freeze

      class Error < ::StandardError; end

      module_function

      # The command as an argument list. +command+ is a shell-like string (the
      # svgbob-command attribute) or nil for the bundled Python port.
      def command(command, python)
        if command && !command.empty?
          ::Shellwords.split command
        else
          bootstrap = %(import sys; sys.path.insert(0, #{VENDOR_DIR.inspect}); ) +
                      %(from svgbob.__main__ import main; main())
          [python || 'python3', '-I', '-c', bootstrap]
        end
      end

      # Renders +source+ with the svgbob +options+ (a Hash of option name to
      # value) and returns the SVG as a UTF-8 string.
      def render(source, options, cmd)
        args = cmd.dup
        options.each {|name, value| args << %(--#{name}) << value.to_s unless value.nil? }
        source = source.end_with?(?\n) ? source : %(#{source}\n)
        begin
          out, err, status = ::Open3.capture3(*args, stdin_data: source.encode('UTF-8'), binmode: true)
        rescue ::SystemCallError => e
          raise Error, %(could not run #{args[0]}: #{e.message})
        end
        unless status.success?
          detail = err.force_encoding('UTF-8').strip
          raise Error, %(#{args[0]} failed (#{status.exitstatus})#{detail.empty? ? '' : ': ' + detail.lines.last.strip})
        end
        svg = out.force_encoding('UTF-8').rstrip
        raise Error, %(#{args[0]} produced no SVG) unless svg.start_with? '<svg'
        svg
      end

      # Widens (and if needed heightens) the SVG so that text labels fit.
      #
      # svgbob sizes the canvas from the line art only, so a label that runs
      # past the rightmost line, or sits below the lowest one, is clipped.
      # A label is assumed to advance 8.6 px per character at a 14 px font
      # (fallback monospace fonts are a little wider than svgbob's 8 px
      # cell). The canvas then reaches 16 px past the end of the longest
      # label, and, when a label's descenders would be cut off at the
      # bottom, 20 px below its baseline: the room svgbob leaves around its
      # own line art at the default scale. svgbob does not
      # scale the font with --scale, so neither do these margins.
      def fit_text(svg, font_size: 14)
        em = font_size / 14.0
        char_w = 8.6 * em
        width = svg[/\A<svg\b[^>]*?\swidth="([\d.]+)"/, 1]
        height = svg[/\A<svg\b[^>]*?\sheight="([\d.]+)"/, 1]
        return svg unless width && height
        right = bottom = 0.0
        svg.scan(%r{<text x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]*)</text>}) do |x, y, text|
          right = [right, x.to_f + char_w * display_width(unescape(text)) + 16 * em].max
          # only when the descenders (0.25 em) would be cut off
          bottom = [bottom, y.to_f + 20 * em].max if y.to_f + 3.5 * em > height.to_f
        end
        new_width = [width.to_f, right.floor.to_f].max
        new_height = [height.to_f, bottom.floor.to_f].max
        return svg if new_width == width.to_f && new_height == height.to_f
        w = format_number new_width
        h = format_number new_height
        svg = svg.sub(/\A(<svg\b[^>]*?\swidth=")[\d.]+(")/) { %(#{$1}#{w}#{$2}) }
        svg = svg.sub(/\A(<svg\b[^>]*?\sheight=")[\d.]+(")/) { %(#{$1}#{h}#{$2}) }
        svg.sub(/(<rect class="backdrop" x="0" y="0" width=")[\d.]+(" height=")[\d.]+(")/) do
          %(#{$1}#{w}#{$2}#{h}#{$3})
        end
      end

      # The width and height of the SVG in px, as numbers.
      def size(svg)
        width = svg[/\A<svg\b[^>]*?\swidth="([\d.]+)"/, 1]
        height = svg[/\A<svg\b[^>]*?\sheight="([\d.]+)"/, 1]
        [width && width.to_f, height && height.to_f]
      end

      def unescape(text)
        text.gsub('&lt;', '<').gsub('&gt;', '>').gsub('&quot;', '"').gsub('&#39;', "'").gsub('&amp;', '&')
      end

      WIDE_CHARS = /[\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}　-〿！-｠￠-￦\u{1f300}-\u{1faff}]/

      # Characters, with East Asian wide characters and emoji counted twice.
      def display_width(text)
        text.length + text.scan(WIDE_CHARS).length
      end

      def format_number(value)
        value == value.floor ? value.to_i.to_s : value.to_s
      end
    end
  end
end
