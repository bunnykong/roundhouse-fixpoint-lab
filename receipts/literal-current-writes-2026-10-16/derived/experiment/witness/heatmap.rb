# literal-transfer boundary witness: load the pinned HeatmapHelper verbatim and observe each result_arr write.
# The only shim is Array#pluck for an Array of Hash records, as in ActiveSupport.
require 'json'
require 'digest'
root, output = ARGV
abort 'usage: heatmap.rb CHATWOOT_ROOT OUT.json' unless root && output
relative = 'app/helpers/api/v2/accounts/heatmap_helper.rb'
path = File.expand_path(File.join(root, relative))
source = File.read(path)
append_line = source.lines.index { |line| line.strip == 'result_arr << row' } + 1
module Api; module V2; module Accounts; end; end; end
class Array
  def pluck(key) = map { |record| record[key] }
end
load path
class HeatmapWitness
  include Api::V2::Accounts::HeatmapHelper
end

def shape(value)
  case value
  when Array
    { 'class' => 'Array', 'elems' => value.map { |v| shape(v) }.uniq }
  when Hash
    { 'class' => 'Hash', 'pairs' => value.map { |k,v| [shape(k), shape(v)] }.uniq }
  else
    { 'class' => value.class.name, 'ancestors' => value.class.ancestors.map(&:to_s) }
  end
end

cases = {
  'empty' => [],
  'complete' => [
    { date: '2026-10-15', hour: 0, value: 0 }, { date: '2026-10-16', hour: 0, value: 2 },
    { date: '2026-10-15', hour: 1, value: 3 }, { date: '2026-10-16', hour: 1, value: 4 }
  ],
  'sparse' => [
    { date: '2026-10-15', hour: 0, value: 1 }, { date: '2026-10-16', hour: 1, value: 4 }
  ]
}
probes = Hash.new { |h,k| h[k] = [] }
coverage = Hash.new(0)
events = []
active_case = nil
trace = TracePoint.new(:line, :b_return, :return) do |tp|
  next unless tp.path == path && tp.method_id == :group_traffic_data
  if tp.event == :line
    coverage[tp.lineno] += 1
    if tp.lineno == append_line
      value = tp.binding.local_variable_get(:result_arr)
      probes['result_arr_before_push'] << shape(value)
      events << { case: active_case, event: 'before result_arr << row', line: tp.lineno,
                  result_arr: Marshal.load(Marshal.dump(value)) }
    end
  elsif tp.event == :b_return && tp.binding.local_variable_defined?(:result_arr)
    value = tp.binding.local_variable_get(:result_arr)
    # The outer each block returns result_arr from its final << expression.
    # The nested dates block returns row, a distinct Array; object identity separates them.
    if tp.return_value.equal?(value)
      probes['outer_block_result'] << shape(tp.return_value)
      events << { case: active_case, event: 'outer each block return', line: tp.lineno,
                  value: Marshal.load(Marshal.dump(tp.return_value)) }
    end
  elsif tp.event == :return
    probes['method_return'] << shape(tp.return_value)
  end
end
returns = {}
trace.enable do
  cases.each do |name, data|
    active_case = name
    returns[name] = HeatmapWitness.new.send(:group_traffic_data, data)
  end
end
abort 'outer block observation missing' if probes['outer_block_result'].empty?
abort 'before-push observation missing' if probes['result_arr_before_push'].empty?
probes.transform_values!(&:uniq)
receipt = { ruby: RUBY_DESCRIPTION, source: relative, source_sha256: Digest::SHA256.hexdigest(source),
  source_execution: 'full pinned module loaded verbatim; private method called on included host',
  shim: 'Array#pluck(key) maps Hash records by that key',
  inputs: cases, returns: returns, probes: probes, events: events,
  executed_lines: coverage.sort.to_h, append_line: append_line,
  writes_covered: ['result_arr = []', 'header result_arr <<', 'row initialization',
                   'nested date row << (Integer or nil)', 'outer result_arr << row'] }
File.write(output, JSON.pretty_generate(receipt) + "\n")
puts JSON.generate(returns)
