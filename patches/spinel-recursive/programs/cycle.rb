# Recursive operations on public JSON values.
def walk_0(value)
  if value.is_a?(Hash)
    value.transform_values { |v| walk_1(v) }
  elsif value.is_a?(Array)
    value.map { |v| walk_1(v) }
  else
    value
  end
end

def walk_1(value)
  if value.is_a?(Hash)
    value.transform_values { |v| walk_0(v) }
  elsif value.is_a?(Array)
    value.map { |v| walk_0(v) }
  else
    value
  end
end

input = { "a" => [1, { "b" => "x" }], "c" => { "d" => [nil, 7, [8, "y"]] } }
n = ARGV.empty? ? 1 : ARGV[0].to_i
result = nil
n.times { result = walk_0(input) }
puts result.inspect
