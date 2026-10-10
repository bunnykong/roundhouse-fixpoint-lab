# Sum Integer leaves in a recursive Hash/Array tree; String and nil leaves contribute zero.
def sum_leaves(value)
  case value
  when Hash
    total = 0
    value.each_value { |v| total += sum_leaves(v) }
    total
  when Array
    total = 0
    value.each { |v| total += sum_leaves(v) }
    total
  when Integer
    value
  else
    0
  end
end

input = { "a" => [1, { "b" => [2, 3, [4, nil]] }], "c" => [5, { "d" => [6, 7, "x"] }] }
n = ARGV.empty? ? 1 : ARGV[0].to_i
result = 0
n.times { result = sum_leaves(input) }
puts result
