# Recursive operations on public JSON values.
def canonical(value)
  case value
  when Hash then value.sort.to_h { |k, v| [k.to_s, canonical(v)] }
  when Array then value.map { |v| canonical(v) }
  else value
  end
end

n = ARGV.empty? ? 1 : ARGV[0].to_i
result = nil
n.times do
  inner = canonical({ "b" => [1, "x"] })
  result = canonical({ "a" => inner.merge("d" => 2), "c" => [inner.merge("e" => nil)] })
end
puts result.inspect
