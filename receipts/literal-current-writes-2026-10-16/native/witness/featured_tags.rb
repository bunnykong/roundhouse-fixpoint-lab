# literal-transfer runtime witness: Mastodon ProcessHashtagsService#update_featured_tags!.
#
# Executes the pinned method source verbatim on stand-ins: `Tag` records with
# Integer ids (what Tag.find_or_create_by_names and status.tags.to_a return),
# a status, and an account whose featured_tags relation records the keyword
# hash passed to `where`. Records runtime shapes at method exit (TracePoint
# :return binding). A boundary witness: no Rails, no database.
#
# Usage: ruby featured_tags.rb INPUT_ROOT OUT.json
require 'json'
require 'digest'
require 'time'

root, out = ARGV
abort 'usage: featured_tags.rb INPUT_ROOT OUT.json' unless root && out
rel = 'app/services/process_hashtags_service.rb'
text = File.read(File.join(root, rel))
lines = text.lines
start = lines.index { |l| l =~ /\A(\s*)def update_featured_tags!/ } or raise 'no def'
indent = lines[start][/\A\s*/]
stop = (start + 1...lines.size).find { |i| lines[i] =~ /\A#{indent}end\b/ } or raise 'no end'
method_src = lines[start..stop].join

class Tag
  attr_reader :id, :name
  def initialize(id, name) = (@id, @name = id, name)
end
FeaturedTag = Struct.new(:tag_id) do
  def increment(_at) = nil
  def decrement(_status) = nil
end
class FeaturedTagsRelation
  attr_reader :where_args
  def initialize(rows) = (@rows, @where_args = rows, [])
  def where(**kw)
    @where_args << kw
    self
  end
  def find_each(&block) = (@rows.each(&block); nil)
end
WStatus = Struct.new(:distributable, :created_at) do
  def distributable? = distributable
end
WAccount = Struct.new(:featured_tags)

class Witness; end
Witness.class_eval(method_src)
Witness.send(:public, :update_featured_tags!)

def shape(v)
  case v
  when Array then { 'class' => 'Array', 'elems' => v.map { |x| shape(x) }.uniq }
  when Hash then { 'class' => 'Hash', 'pairs' => v.map { |k, x| [shape(k), shape(x)] }.uniq }
  else { 'class' => v.class.name, 'ancestors' => v.class.ancestors.map(&:to_s) }
  end
end

t1, t2, t3 = Tag.new(1, 'ruby'), Tag.new(2, 'rails'), Tag.new(3, 'mastodon')
cases = {
  'added and removed' => [true, [t1, t2], [t2, t3]],
  'only removed' => [true, [], [t1]],
  'only added' => [true, [t1, t3], []],
  'unchanged' => [true, [t2], [t2]],
  'not distributable' => [false, [t1], [t3]]
}

probes = Hash.new { |h, k| h[k] = [] }
results = cases.map do |label, (dist, current, previous)|
  rel_stub = FeaturedTagsRelation.new([FeaturedTag.new(1)])
  w = Witness.new
  w.instance_variable_set(:@status, WStatus.new(dist, Time.utc(2026, 10, 15)))
  w.instance_variable_set(:@account, WAccount.new(rel_stub))
  w.instance_variable_set(:@current_tags, current)
  w.instance_variable_set(:@previous_tags, previous)
  locals = {}
  tp = TracePoint.new(:return) do |t|
    next unless t.method_id == :update_featured_tags!
    %i[added_tags removed_tags].each do |n|
      locals[n] = t.binding.local_variable_get(n) if t.binding.local_variable_defined?(n)
    end
  end
  ret = tp.enable { w.update_featured_tags! }
  probes['current_tags'] << shape(current)
  probes['return_value'] << shape(ret)
  %i[added_tags removed_tags].each { |n| probes[n.to_s] << shape(locals[n]) if locals.key?(n) && !locals[n].nil? }
  rel_stub.where_args.each do |kw|
    probes['where_kwargs'] << shape(kw)
    kw.each_value { |ids| probes['ids'] << shape(ids); ids.each { |i| probes['id_value'] << shape(i) } }
  end
  (current + previous).each { |tag| probes['tag_elem'] << shape(tag) }
  # `map(&:id)` calls Symbol#to_proc once per element: record those calls.
  idp = :id.to_proc
  [locals[:added_tags], locals[:removed_tags]].compact.each do |tags|
    next if tags.empty?
    probes['id_block'] << { 'class' => 'Proc', 'args' => tags.map { |t| [shape(t)] }.uniq,
                            'returns' => tags.map { |t| shape(idp.call(t)) }.uniq }
  end
  { 'case' => label, 'return_value' => shape(ret), 'locals' => locals.transform_values { |v| shape(v) },
    'where_kwargs' => rel_stub.where_args.map { |kw| shape(kw) } }
end

doc = {
  'witness' => 'mastodon-process-hashtags-update-featured-tags',
  'ruby' => RUBY_DESCRIPTION,
  'source' => rel,
  'source_sha256' => Digest::SHA256.hexdigest(text),
  'declarations' => ['ProcessHashtagsService#update_featured_tags!'],
  'stand_ins' => 'Tag(id: Integer); FeaturedTag; featured_tags relation recording where(**kw); status; account',
  'probes' => probes.transform_values(&:uniq),
  'cases' => results
}
File.write(out, JSON.pretty_generate(doc) + "\n")
puts JSON.generate(doc['probes'].transform_values { |v| v.map { |x| x['class'] }.uniq })
