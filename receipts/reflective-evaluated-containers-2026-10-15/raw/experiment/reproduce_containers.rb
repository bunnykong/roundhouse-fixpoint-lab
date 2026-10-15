require "json"
require "digest"
require_relative "week/bound-next/sources/probe-source/src/analyze/fixpoint_bound/fixtures/reflective_array"
require_relative "week/bound-next/sources/probe-source/src/analyze/fixpoint_bound/fixtures/reflective_containers"
require_relative "week/bound-next/sources/probe-source/src/analyze/fixpoint_bound/fixtures/reflective_neighbours"

rows = []
[[BoundEntranceWitness, [:write]],
 [ContainerEntranceWitness, ContainerEntranceWitness.instance_methods(false).grep(/^write_/).sort],
 [NeighbourEntranceWitness, NeighbourEntranceWitness.instance_methods(false).grep(/^write_/).sort]].each do |klass, methods|
  methods.each do |method|
    witness = klass.new
    witness.public_send(method)
    raise "write absent" unless witness.instance_variable_defined?(:@x)
    value = witness.instance_variable_get(:@x)
    shape = value.is_a?(Hash) ? "hash" : "array"
    value = value.fetch(:key) if value.is_a?(Hash)
    depth = 0
    while value.is_a?(Array)
      raise "expected singleton" unless value.length == 1
      depth += 1
      value = value.first
    end
    raise "wrong runtime value" unless depth == 17 && value == 1
    rows << { fixture: klass.name, method: method, stored: true, shape: shape, array_depth: depth, leaf: value }
  end
end
raise "empty or missing fixture" unless rows.length == 15
deferred = [:defer_in_array, :query_in_array].map do |method|
  witness = NeighbourEntranceWitness.new
  witness.public_send(method)
  raise "deferred expression executed a write" if witness.instance_variable_defined?(:@x)
  { method: method, stored: false }
end
puts JSON.pretty_generate(condition: "reflective-array-20261015-fe6b169e", ruby: RUBY_VERSION,
  runtime: RUBY_DESCRIPTION, cases: rows, deferred_controls: deferred, timed_measurement: false,
  scope: "Native CRuby execution; no emitted-code equivalence claim")
