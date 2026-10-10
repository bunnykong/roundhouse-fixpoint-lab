#!/usr/bin/env ruby
# Scan only public app/lib Ruby sources, using Prism's decoded string-literal value.
require 'json'
require 'prism'
root = ARGV.fetch(0)
rows = %w[campfire mastodon chatwoot forem discourse].map do |name|
  abort "missing app directory: #{name}" unless Dir.exist?(File.join(root, name, 'app'))
  calls = []
  files = 0
  parse_errors = 0
  visit = lambda do |node, file|
    return unless node
    if node.is_a?(Prism::CallNode) && %i[send public_send __send__ try].include?(node.name)
      arg = node.arguments&.arguments&.first
      if arg.is_a?(Prism::StringNode)
        calls << { file: file, line: node.location.start_line, bytes: arg.unescaped.bytesize }
      end
    end
    node.child_nodes.each { |child| visit.call(child, file) }
  end
  %w[app lib].each do |dir|
    Dir.glob(File.join(root, name, dir, '**', '*.rb')).sort.each do |path|
      parsed = Prism.parse_file(path)
      files += 1
      parse_errors += parsed.errors.size
      visit.call(parsed.value, path.delete_prefix(File.join(root, name) + '/'))
    end
  end
  { app: name, ruby_files: files, parse_errors: parse_errors, literal_calls: calls.size,
    over_80_bytes: calls.select { |c| c[:bytes] > 80 } }
end
puts JSON.pretty_generate({ ruby: RUBY_VERSION, prism: Prism::VERSION, scope: 'app/ and lib/', rows: rows })
abort 'long literal dispatch calls found' unless rows.all? { |r| r[:over_80_bytes].empty? }
