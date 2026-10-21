# CRuby witness for three of the 21 catalog operators: what each returns once its Pending operand resolves.
require "json"
require "bigdecimal"
require "date"

def outcome(label)
  v = yield
  { expr: label, class: v.class.name, value: v.inspect[0, 40] }
rescue Exception => e
  { expr: label, raises: e.class.name }
end

rows = []
# dispatch/Int/{+,-,*,/}/arg: pre-patch f(P) = Int; the harness's f(BigDecimal) = BigDecimal.
{ "Integer" => 2, "Float" => 2.5, "BigDecimal" => BigDecimal("2"), "Rational" => Rational(1, 2), "nil" => nil }.each do |n, x|
  %w[+ - * /].each { |op| rows << outcome("1 #{op} #{n}") { 1.public_send(op, x) } }
end
# dispatch/Array/{first,last,sample}/arg: pre-patch f(P) = A[Int]; the harness's f(BigDecimal) = (Int|Nil).
a = [1, 2, 3]
{ "none" => [], "Integer" => [2], "BigDecimal" => [BigDecimal("2")], "Float" => [2.7], "nil" => [nil] }.each do |n, args|
  %w[first last sample take].each { |m| rows << outcome("[1,2,3].#{m}(#{n})") { a.public_send(m, *args) } }
end
{ "Integer" => [1], "Range" => [0..1], "start,len" => [0, 2], "BigDecimal" => [BigDecimal("1")] }.each do |n, args|
  rows << outcome("[1,2,3][#{n}]") { a[*args] }
end
# date_constructor/*/arg0: pre-patch f(P) = Date; the harness's f(BigDecimal) = U.
{ "String" => "2026-10-22", "nil" => nil, "BigDecimal" => BigDecimal("2026"), "Integer" => 2026 }.each do |n, x|
  rows << outcome("Date.parse(#{n})") { Date.parse(x) }
  rows << outcome("Date.new(#{n})") { Date.new(x) }
  rows << outcome("Date.iso8601(#{n})") { Date.iso8601(x) }
end
# dispatch/to_h/receiver: pre-patch f(P) = H[P,P]; the harness's f(BigDecimal) = U.
S = Struct.new(:a)
{ "nil" => nil, "pairs" => [[:a, 1]], "Hash" => { a: 1 }, "Struct" => S.new(1), "BigDecimal" => BigDecimal("1") }.each do |n, x|
  rows << outcome("#{n}.to_h") { x.to_h }
end
puts JSON.generate(ruby: RUBY_DESCRIPTION, bigdecimal: BigDecimal::VERSION, date: Date::VERSION, rows: rows)
