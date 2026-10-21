# Shared helpers for the minimal witnesses: pinned sources, unchanged methods and value types.
# Needs CRuby 4.0.7 and its bundled Prism. No analyzer runs here.
require 'digest'
require 'json'
require 'prism'

unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'
  abort "These witnesses are pinned to CRuby 4.0.7; this is #{RUBY_DESCRIPTION}"
end

LAB_ROOT = File.expand_path('../../..', __dir__)
APPS = ENV.fetch('APPS', File.join(LAB_ROOT, 'corpus', 'apps'))

# The path of a pinned application file, after checking its SHA-256.
def pinned(app, path, sha256)
  file = File.join(APPS, app, path)
  abort "missing #{file}; set APPS to a directory of pinned app checkouts" unless File.file?(file)
  actual = Digest::SHA256.file(file).hexdigest
  abort "#{app}/#{path}: SHA-256 #{actual}, expected #{sha256}" unless actual == sha256
  file
end

# Define one unchanged method from a pinned file on `target`, keeping its file name and line numbers.
def install(target, file, name)
  found = []
  queue = [Prism.parse_file(file).value]
  while (node = queue.shift)
    found << node if node.is_a?(Prism::DefNode) && node.name == name
    queue.concat(node.compact_child_nodes)
  end
  abort "#{file}: #{found.size} definitions of #{name}" unless found.size == 1
  target.module_eval(found.first.location.slice, file, found.first.location.start_line)
end

# The exact source text between two byte offsets of a pinned file.
def span(file, start, finish)
  File.binread(file).byteslice(start...finish).force_encoding(Encoding::UTF_8)
end

# The runtime type encoding the census used for membership checks.
def value_type(value)
  case value
  when Hash
    { kind: 'hash', key: join(value.keys.map { |x| value_type(x) }), value: join(value.values.map { |x| value_type(x) }) }
  when Array then { kind: 'array', elem: join(value.map { |x| value_type(x) }) }
  when String then { kind: 'str' }
  when Symbol then { kind: 'sym' }
  when Integer then { kind: 'int' }
  when Float then { kind: 'float' }
  when TrueClass, FalseClass then { kind: 'bool' }
  when NilClass then { kind: 'nil' }
  when Time then { kind: 'time' }
  when Module then { kind: 'class', id: value.name, args: [] }
  else { kind: 'class', id: value.class.name, args: [] }
  end
end

def join(types)
  types = types.uniq
  return { kind: 'bottom' } if types.empty?
  return types.first if types.size == 1

  { kind: 'union', variants: types }
end

# One JSON line per observed row, read by check.py.
def emit(row, value, app:, path:, line:, boundary:)
  puts JSON.generate(row: row, app: app, source: path, line: line, ruby: RUBY_DESCRIPTION,
                     ruby_class: value.class.name, inspect: value.inspect, type: value_type(value),
                     boundary: boundary)
end
