require 'json'
require_relative 'fixtures/issue964/lib/prefs'
WidgetValue = Struct.new(:prefs, :name)
w = WidgetValue.new({'mode' => 'advanced', 'lang' => 7}, '{"lang":17}')
rows = [
  ['mode', Prefs.mode(w), 'String'],
  ['c', Prefs.c(w), 'Hash'],
  ['d', Prefs.d(JSON.parse(w.name)), 'Integer'],
  ['e', Prefs.e(w), 'Integer'],
  ['mode-fallback', Prefs.mode(WidgetValue.new({}, '{}')), 'Symbol'],
  ['d-fallback', Prefs.d({}), 'Symbol'],
  ['e-fallback', Prefs.e(WidgetValue.new({}, '{}')), 'String']
]
raise 'witness mismatch' unless rows.all? { |_,value,expected| value.class.name == expected }
puts JSON.pretty_generate({ruby: RUBY_DESCRIPTION, rows: rows.map { |method,value,expected|
  {method: method, value: value, runtime_class: value.class.name, expected_class: expected}
}})
