require 'rubygems'
local_paths = ENV.fetch('WITNESS_GEM_ROOTS').split(File::PATH_SEPARATOR) + Gem.path
Gem.use_paths(local_paths.first, local_paths)
require 'json'
require 'prism'
require 'digest'
raise RUBY_DESCRIPTION unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'

INPUTS = File.expand_path(ENV.fetch('PUBLIC_INPUTS'))
CAMPFIRE = File.expand_path(ENV.fetch('CAMPFIRE_INPUT'))
ROWS = JSON.parse(File.read(File.join(__dir__, 'classified-drops.json'))).to_h { |r| [r['id'], r] }
SOURCES = []
OBSERVATIONS = []

def source_record(path, **extra)
  SOURCES << { path: path, sha256: Digest::SHA256.file(path).hexdigest, **extra }
end

def nodes_in(path)
  ast = Prism.parse_file(path)
  raise ast.errors.inspect unless ast.success?
  all = []
  walk = lambda do |node|
    next unless node
    all << node
    node.compact_child_nodes.each { |child| walk.call(child) }
  end
  walk.call(ast.value)
  all
end

def install_method(target, path, name)
  found = nodes_in(path).select { |node| node.is_a?(Prism::DefNode) && node.name == name.to_sym }
  raise "#{path}: #{name}: #{found.size} definitions" unless found.size == 1
  loc = found.first.location
  target.module_eval(loc.slice, path, loc.start_line)
  source_record(path, method: name, start: loc.start_offset, end: loc.end_offset, line: loc.start_line)
end

def concrete_type(value)
  case value
  when Hash
    { kind: 'hash', key: join_types(value.keys.map { |x| concrete_type(x) }),
      value: join_types(value.values.map { |x| concrete_type(x) }) }
  when Array then { kind: 'array', elem: join_types(value.map { |x| concrete_type(x) }) }
  when String then { kind: 'str' }
  when Symbol then { kind: 'sym' }
  when Integer then { kind: 'int' }
  when Float then { kind: 'float' }
  when TrueClass, FalseClass then { kind: 'bool' }
  when NilClass then { kind: 'nil' }
  when Time then { kind: 'time' }
  when Range then { kind: 'class', id: 'Range', args: [join_types([concrete_type(value.begin), concrete_type(value.end)])] }
  else
    # Keep named Ruby types, including Rails Parameters and collection proxies.
    # Arel's analyzer spelling is recorded separately, never substituted silently.
    if defined?(ActiveRecord::Relation) && value.is_a?(ActiveRecord::Relation)
      { kind: 'relation', of: value.klass.name }
    else
      { kind: 'class', id: value.class.name, args: [] }
    end
  end
end

def join_types(types)
  types = types.uniq
  return { kind: 'bottom' } if types.empty?
  return types.first if types.size == 1
  { kind: 'union', variants: types }
end

def observe(label, value, row_ids = [], **details)
  # Do not query a relation merely to display it.
  shown = if defined?(ActiveRecord::Relation) && value.is_a?(ActiveRecord::Relation)
            "#<#{value.class.name}[#{value.klass.name}]>"
          else
            value.inspect
          end
  OBSERVATIONS << { label: label, rows: row_ids, ruby_class: value.class.name,
                    ancestors: value.class.ancestors.filter_map(&:name),
                    inspect: shown, type: concrete_type(value), **details }
  value
end

def context_with_params(params)
  klass = Class.new do
    attr_accessor :params
  end
  klass.new.tap { |object| object.params = params }
end

def eval_at(context, text, path, line, locals = {})
  b = context.instance_eval { binding }
  locals.each { |k, v| b.local_variable_set(k, v) }
  eval(text, b, path, line)
end

def call_argument(path, line, name, rows, context: Object.new, locals: {}, index: 0, occurrence: 0)
  calls = nodes_in(path).select { |n| n.is_a?(Prism::CallNode) && n.name == name.to_sym && n.message_loc&.start_line == line }
  raise "missing #{path}:#{line} #{name}" unless calls[occurrence]
  call = calls[occurrence]
  arg = call.arguments.arguments.fetch(index)
  text = arg.location.slice
  # Ruby keyword arguments form the Hash that the parameter row describes.
  runnable = arg.is_a?(Prism::KeywordHashNode) ? "{#{text}}" : text
  value = eval_at(context, runnable, path, line, locals)
  source_record(path, call: call.location.slice, argument: text, line: line,
                start: arg.location.start_offset, end: arg.location.end_offset)
  observe("#{File.basename(path)}:#{line}:#{name}[#{index}]", value, rows,
          source: path, line: line, expression: text, boundary: 'unchanged source argument; caller reachability in source-proofs.json')
end

def public_input_path(path)
  prefix = 'examples/apps/'
  raise "unsupported public input path: #{path}" unless path.start_with?(prefix)
  app, rest = path.delete_prefix(prefix).split('/', 2)
  root = app == 'campfire' ? CAMPFIRE : File.join(INPUTS, app)
  File.join(root, rest)
end

def exact_expression(id, locals = {}, context: Object.new)
  row = ROWS.fetch(id)
  path = public_input_path(row.fetch('source'))
  source = File.binread(path)
  raise 'source changed' unless Digest::SHA256.hexdigest(source) == row.fetch('source_sha256')
  expr = source.byteslice(row['span']['start']...row['span']['end'])
  raise 'span mismatch' unless expr == row.fetch('expression')
  source_record(path, line: row['line'], start: row['span']['start'], end: row['span']['end'])
  runnable = row['node'] == 'Hash' && !expr.lstrip.start_with?('{') ? "{#{expr}}" : expr
  observe("exact-expression-#{id}", eval_at(context, runnable, path, row['line'], locals), [id],
          expression: expr, source: path, line: row['line'])
end

def finish(name)
  File.write(File.join(ENV.fetch('WITNESS_OUTPUT', __dir__), name), JSON.pretty_generate(
    ruby: RUBY_DESCRIPTION, sources: SOURCES.uniq,
    gems: Gem.loaded_specs.transform_values { |s| { version: s.version.to_s, path: s.full_gem_path } },
    observations: OBSERVATIONS
  ) + "\n")
  puts "#{name}: #{OBSERVATIONS.size} observations"
end
