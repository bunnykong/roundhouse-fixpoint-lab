require "json"
require_relative "reflective_called_closures"

rows = CalledClosureWitness.instance_methods(false).reject { |m| m == :sink }.sort.map do |method|
  witness = CalledClosureWitness.new
  witness.public_send(method)
  written = witness.instance_variable_defined?(:@x)
  expected = !method.to_s.start_with?("deferred_")
  raise "wrong execution for #{method}" unless written == expected
  row = {method: method, written: written, expected: expected}
  if written
    value = witness.instance_variable_get(:@x)
    row[:shape] = value.is_a?(Hash) ? "hash" : "array"
    value = value.fetch(:key) if value.is_a?(Hash)
    depth = 0
    while value.is_a?(Array)
      raise "expected singleton array" unless value.length == 1
      depth += 1
      value = value.first
    end
    raise "wrong native value" unless depth == 17 && value == 1
    row.merge!(array_depth: depth, leaf: value)
  end
  row
end
raise "missing cases" unless rows.length == 13
puts JSON.pretty_generate(condition: "rv-reflective-evaluated-containers-20261015/closures",
  ruby: RUBY_DESCRIPTION, cases: rows)
