require 'digest'
require 'fileutils'
require 'json'

module Asciidoctor
  module Svgbob
    # The work shared by the block and the block macro: render the diagram
    # (or reuse the cached SVG) and return the image block that replaces it.
    module Processing
      include ::Asciidoctor::Logging

      OFF_VALUES = %w(off false no 0).freeze

      # +attrs+ are the block attributes, +default_name+ the image name to use
      # when the block has no target (nil: derived from the checksum).
      def svgbob_block(parent, source, attrs, location, default_name = nil)
        doc = parent.document
        attrs = attrs.dup
        orig_attrs = attrs.dup
        attrs.delete_if {|key, _| ::Integer === key }
        %w(style cloaked-context).each {|key| attrs.delete key }
        format = (attrs.delete('format') || doc.attr('svgbob-format', 'svg')).to_s
        title = attrs.delete 'title'
        caption = attrs.delete 'caption'

        block = case format
                when 'svg'
                  image_block parent, source, attrs, default_name
                when 'txt'
                  attrs.delete 'target'
                  ::Asciidoctor::Block.new parent, :literal, source: source, attributes: attrs
                else
                  raise Renderer::Error, %(unsupported format #{format}, use svg or txt)
                end
        block.title = title if title
        block.assign_caption caption, 'figure'
        block
      rescue Renderer::Error, ::SystemCallError => e
        raise if doc.attr('svgbob-on-error') == 'abort'
        text = %(Failed to generate image: #{e.message})
        logger.error message_with_context %(svgbob: #{text}), source_location: location
        ::Asciidoctor::Block.new parent, :listing, source: %(#{text}\n#{source}), attributes: orig_attrs
      end

      private

      def image_block(parent, source, attrs, default_name)
        doc = parent.document
        options = {}
        Renderer::OPTIONS.each do |name|
          value = attrs.delete(name) || doc.attr(%(svgbob-#{name}))
          options[name] = value.to_s unless value.nil? || value.to_s.empty?
        end
        fit = attrs.delete('fit-text') || doc.attr('svgbob-fit-text', 'on')
        fit = !OFF_VALUES.include?(fit.to_s.downcase)
        cmd = Renderer.command doc.attr('svgbob-command'), doc.attr('svgbob-python')

        checksum = ::Digest::SHA256.hexdigest [VERSION, cmd, options.sort, fit, source].inspect
        image_name = %(#{attrs.delete('target') || default_name || %(svgbob-#{checksum[0, 12]})}.svg)
        image_file = system_path doc, image_name, image_output_dir(parent)
        cache_file = system_path doc, %(#{image_name}.cache), cache_dir(doc)

        nocache = attrs['nocache-option'] || doc.attr?('svgbob-nocache')
        metadata = nil
        if !nocache && ::File.exist?(cache_file) && ::File.exist?(image_file)
          metadata = (::JSON.parse ::File.read(cache_file) rescue nil)
          metadata = nil unless metadata && metadata['checksum'] == checksum
        end

        unless metadata
          svg = Renderer.render source, options, cmd
          if fit
            svg = Renderer.fit_text svg, font_size: (options['font-size'] || 14).to_f
          end
          width, height = Renderer.size svg
          metadata = { 'checksum' => checksum, 'width' => width, 'height' => height }
          ::FileUtils.mkdir_p ::File.dirname(image_file)
          ::File.write image_file, svg, mode: 'wb'
          if nocache
            ::File.delete cache_file if ::File.exist? cache_file
          else
            ::FileUtils.mkdir_p ::File.dirname(cache_file)
            ::File.write cache_file, ::JSON.dump(metadata)
          end
        end

        doc.register :images, image_name
        node = ::Asciidoctor::Block.new parent, :image, content_model: :empty, attributes: attrs

        alt = node.attr('alt') ||
              (::File.basename(image_name, '.svg').tr '_-', ' ')
        node.set_attr 'alt', parent.sub_specialchars(alt)

        if (scaledwidth = node.attr 'scaledwidth') && scaledwidth =~ /\d\z/
          node.set_attr 'scaledwidth', %(#{scaledwidth}%)
        end

        if /html/i =~ doc.attr('backend').to_s
          node.set_attr 'width', metadata['width'].to_i.to_s if metadata['width'] && !node.attr?('width')
          node.set_attr 'height', metadata['height'].to_i.to_s if metadata['height'] && !node.attr?('height')
        end

        node.set_attr 'target', image_target(parent, node, image_file, image_name)
        node
      end

      # The image target. The HTML converter links to it relative to the
      # output (outdir + imagesdir); data-uri, inline SVG and the PDF
      # converter read it relative to the document (base_dir + imagesdir).
      # When the image is not under that directory, an absolute path is used
      # for reading and the bare name for linking.
      def image_target(parent, node, image_file, image_name)
        doc = parent.document
        reads_file = doc.attr?('data-uri') || node.option?('inline') || doc.backend == 'pdf'
        imagesdir = parent.attr('imagesdir', nil, true) || ''
        return image_name if imagesdir.include? '://'
        read_dir = system_path doc, imagesdir, (reads_file ? doc.base_dir : output_dir(doc))
        if image_file.start_with? %(#{read_dir}/)
          image_file[(read_dir.length + 1)..-1]
        elsif reads_file
          image_file
        else
          image_name
        end
      end

      def image_output_dir(parent)
        doc = parent.document
        if (images_out = parent.attr('imagesoutdir', nil, true))
          system_path doc, images_out, doc.base_dir
        else
          imagesdir = parent.attr('imagesdir', nil, true) || ''
          imagesdir = '' if imagesdir.include? '://'
          system_path doc, imagesdir, output_dir(doc)
        end
      end

      def cache_dir(doc)
        if (dir = doc.attr('svgbob-cachedir'))
          system_path doc, dir, doc.base_dir
        else
          system_path doc, '.asciidoctor/svgbob', output_dir(doc)
        end
      end

      def output_dir(doc)
        system_path doc, (doc.attr('outdir') || doc.options[:to_dir] || doc.base_dir), doc.base_dir
      end

      def system_path(doc, path, base)
        doc.path_resolver.system_path path, base
      end
    end

    # [svgbob, target, format]
    # ....
    # ascii art
    # ....
    class BlockProcessor < ::Asciidoctor::Extensions::BlockProcessor
      include Processing
      use_dsl
      named :svgbob
      on_context :listing, :literal, :open, :paragraph
      content_model :raw
      name_positional_attributes 'target', 'format'

      def process(parent, reader, attrs)
        location = parent.document.reader.cursor_at_mark
        svgbob_block parent, reader.read, attrs, location
      end
    end

    # svgbob::path/to/diagram.bob[format, target=name]
    #
    # The image is named after the file unless a target is given.
    class BlockMacroProcessor < ::Asciidoctor::Extensions::BlockMacroProcessor
      include Processing
      use_dsl
      named :svgbob
      name_positional_attributes 'format'

      def process(parent, target, attrs)
        doc = parent.document
        location = doc.reader.cursor_at_mark
        path = parent.normalize_system_path target, (parent.attr 'docdir', nil, true)
        begin
          source = ::File.read path, mode: 'r:UTF-8'
        rescue ::SystemCallError => e
          logger.error message_with_context %(svgbob: cannot read #{target}: #{e.message}), source_location: location
          return ::Asciidoctor::Block.new parent, :paragraph, source: %(svgbob::#{target}[]), attributes: { 'role' => 'unresolved' }
        end
        svgbob_block parent, source, attrs, location, ::File.basename(target, '.*')
      end
    end
  end
end
