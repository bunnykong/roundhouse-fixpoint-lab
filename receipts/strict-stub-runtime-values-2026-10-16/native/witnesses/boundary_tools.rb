#!/usr/bin/env ruby
# Tiny, source-preserving boundary witnesses; not a full Rails application boot.
require 'json'
require 'prism'
require 'digest'
require 'erb'
abort "CRuby 4.0.7 required: #{RUBY_DESCRIPTION}" unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'

HERE = File.expand_path(__dir__)
INPUTS = File.expand_path(ENV.fetch('PUBLIC_INPUTS'))
SOURCES = []
OBSERVATIONS = []

def install_method(target, path, name)
  source = File.binread(path)
  ast = Prism.parse(source)
  raise ast.errors.inspect unless ast.success?
  found = []
  walk = ->(node) do
    return unless node
    found << node if node.is_a?(Prism::DefNode) && node.name.to_s == name.to_s
    node.compact_child_nodes.each { |child| walk.call(child) }
  end
  walk.call(ast.value)
  raise "Expected one #{name} in #{path}, got #{found.size}" unless found.size == 1
  n = found.first
  target.module_eval(n.location.slice, path, n.location.start_line)
  SOURCES << { path: path, sha256: Digest::SHA256.hexdigest(source), method: name,
               start: n.location.start_offset, end: n.location.end_offset, line: n.location.start_line }
end

def observe(label, value, expected)
  raise "#{label}: expected #{expected}, got #{value.inspect}" unless value.is_a?(expected)
  OBSERVATIONS << { label: label, value: value, ruby_class: value.class.name }
end
