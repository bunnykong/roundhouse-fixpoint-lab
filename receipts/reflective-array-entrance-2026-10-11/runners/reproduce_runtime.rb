require "json"
raise "pass the exact source fixture path" unless ARGV.length == 1
require File.expand_path(ARGV.fetch(0))
witness = BoundEntranceWitness.new
witness.write
value = witness.read
depth = 0
while value.is_a?(Array)
  raise "expected singleton array" unless value.length == 1
  depth += 1
  value = value.first
end
raise "missing Ruby write" unless value == 1 && witness.instance_variable_defined?(:@x)
puts JSON.pretty_generate(
  condition: "reflective-array-entrance-native-array-entrance-20261011-v1",
  ruby: RUBY_VERSION, successful_destination: "x",
  stored: true, array_depth: depth, leaf_class: value.class.name, leaf_value: value
)
