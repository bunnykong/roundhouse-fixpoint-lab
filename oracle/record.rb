#!/usr/bin/env ruby
# Frozen snapshots at Ruby call/return boundaries; no Rails or gems required.
require "json"
require "optparse"
require "digest"

module ShapeOracle
  LEAVES = %w[Integer Float String Symbol nil bool].freeze

  def self.tagged(value, seen = {})
    oid = value.object_id
    return { "ref" => seen[oid] } if seen.key?(oid)
    id = seen.size
    seen[oid] = id
    node = { "id" => id }
    case value
    when Integer, Float
      node.merge!("tag" => value.class.name, "value" => value)
      node["value"] = value.to_s if value.is_a?(Float) && !value.finite?
    when String
      node["tag"] = "String"
      node["encoding"] = value.encoding.name
      utf8 = value.dup.force_encoding(Encoding::UTF_8)
      if utf8.valid_encoding?
        node["value"] = utf8
      else
        node["bytes"] = [value.b].pack("m0")
      end
    when Symbol
      node.merge!("tag" => "Symbol", "value" => value.to_s)
    when NilClass then node["tag"] = "nil"
    when TrueClass then node["tag"] = "true"
    when FalseClass then node["tag"] = "false"
    when Array
      node.merge!("tag" => "Array", "items" => value.map { |v| tagged(v, seen) })
    when Hash
      node.merge!("tag" => "Hash", "entries" => value.map do |k, v|
        { "key" => tagged(k, seen), "value" => tagged(v, seen) }
      end)
    else
      raise TypeError, "unsupported recorded class #{value.class} (no implicit untyped)"
    end
    node
  end

  class Fuzzer
    def initialize(seed, depth, leaves)
      @rng, @depth, @leaves = Random.new(seed), depth, leaves
    end

    def leaf(tag = @leaves.sample(random: @rng))
      case tag
      when "Integer" then @rng.rand(-1_000..1_000)
      when "Float" then @rng.rand * 20 - 10
      when "String" then ["", "x", "snow \u2603", "s#{@rng.rand(100)}"].sample(random: @rng)
      when "Symbol" then "s#{@rng.rand(100)}".to_sym
      when "nil" then nil
      when "bool" then @rng.rand(2).zero?
      end
    end

    def random_value(depth = @depth)
      return leaf if depth.zero? || @rng.rand < 0.5
      if @rng.rand(2).zero?
        Array.new(@rng.rand(0..3)) { random_value(depth - 1) }
      else
        Array.new(@rng.rand(0..3)) do |i|
          ["k#{i}_#{@rng.rand(20)}", random_value(depth - 1)]
        end.to_h
      end
    end

    def sample(index)
      return leaf(@leaves[index]) if index < @leaves.size
      return random_value if @depth.zero?
      case index - @leaves.size
      when 0 then []
      when 1 then {}
      when 2
        value = @leaves.map { |tag| leaf(tag) }
        (@depth - 1).times { |d| value = d.even? ? { "deep" => value } : [value] }
        value
      else random_value
      end
    end
  end

  def self.target(text)
    match = /\A([A-Z]\w*(?:::[A-Z]\w*)*)([#.])(\w+[!?=]?)\z/.match(text)
    raise ArgumentError, "target must be Constant#method or Constant.method: #{text}" unless match
    constant = match[1].split("::").inject(Object) { |c, name| c.const_get(name, false) }
    receiver = if match[2] == "."
      constant
    elsif constant.is_a?(Class)
      constant.new
    else
      Object.new.extend(constant)
    end
    [receiver, match[3].to_sym]
  end

  def self.display_path(path)
    absolute = File.expand_path(path)
    root = File.expand_path("..", __dir__) + File::SEPARATOR
    absolute.start_with?(root) ? absolute.delete_prefix(root) : File.basename(absolute)
  end

  def self.main(argv)
    opts = { sources: [], stubs: [], returns: [], params: [], args: [], prefix: [],
             count: 200, seed: 0, depth: 6, leaves: %w[Integer Float String nil bool] }
    parser = OptionParser.new do |o|
      o.banner = "Usage: ruby record.rb --source FILE --output FILE [--entry Class#action] [--fuzz Class#method]"
      o.on("--source FILE", "Ruby file to load (repeatable)") { |v| opts[:sources] << v }
      o.on("--stub FILE", "Extra stubs, loaded before sources (repeatable)") { |v| opts[:stubs] << v }
      o.on("--output FILE", "Tagged JSONL output; separate from app stdout") { |v| opts[:output] = v }
      o.on("--entry TARGET") { |v| opts[:entry] = v }
      o.on("--args JSON", "Positional entry arguments as a JSON array") { |v| opts[:args] = JSON.parse(v) }
      o.on("--returns NAMES", "Comma-separated method names or Owner#method") { |v| opts[:returns].concat(v.split(",")) }
      o.on("--params SLOTS", "Comma-separated method:param (or Owner#method:param)") { |v| opts[:params].concat(v.split(",")) }
      o.on("--fuzz TARGET", "Call TARGET with each generated value as its last argument") { |v| opts[:fuzz] = v }
      o.on("--prefix-args JSON", "Arguments before the generated value, e.g. [6] for carry") { |v| opts[:prefix] = JSON.parse(v) }
      o.on("--count N", Integer) { |v| opts[:count] = v }
      o.on("--seed N", Integer) { |v| opts[:seed] = v }
      o.on("--depth N", Integer) { |v| opts[:depth] = v }
      o.on("--leaves TAGS", "Default Integer,Float,String,nil,bool; Symbol is opt-in") { |v| opts[:leaves] = v.split(",") }
    end
    parser.parse!(argv)
    raise ArgumentError, parser.banner unless argv.empty? && opts[:output] && !opts[:sources].empty?
    raise ArgumentError, "choose an entry and/or fuzz target, and at least one slot" unless
      (opts[:entry] || opts[:fuzz]) && (!opts[:returns].empty? || !opts[:params].empty?)
    raise ArgumentError, "count/depth must be nonnegative" if opts[:count] < 0 || opts[:depth] < 0
    raise ArgumentError, "args must be JSON arrays" unless opts[:args].is_a?(Array) && opts[:prefix].is_a?(Array)
    raise ArgumentError, "unknown or empty leaf set" if opts[:leaves].empty? || !(opts[:leaves] - LEAVES).empty?
    if (opts[:stubs] + opts[:sources]).any? { |path| File.expand_path(path) == File.expand_path(opts[:output]) }
      raise ArgumentError, "output must not overwrite a source or stub"
    end
    params = opts[:params].map do |text|
      match = /\A(.+):([a-zA-Z_]\w*)\z/.match(text)
      raise ArgumentError, "parameter selector must be method:param: #{text}" unless match
      [match[1], match[2].to_sym]
    end.uniq
    Object.const_set(:ApplicationController, Class.new) unless Object.const_defined?(:ApplicationController)
    opts[:stubs].each { |path| load File.expand_path(path) }
    records = invocations = 0
    File.open(opts[:output], "w") do |out|
      emit = ->(record) { out.puts(JSON.generate(record)) }
      sources = (opts[:stubs] + opts[:sources]).map do |path|
        { "path" => display_path(path), "sha256" => Digest::SHA256.file(path).hexdigest }
      end
      emit.call("kind" => "meta", "format" => "shape-oracle/v1", "ruby" => RUBY_VERSION,
                "sources" => sources, "options" => opts.merge(
                  sources: opts[:sources].map { |p| display_path(p) },
                  stubs: opts[:stubs].map { |p| display_path(p) }, output: display_path(opts[:output])))
      trace = TracePoint.new(:call, :return) do |tp|
        singleton = tp.defined_class.singleton_class?
        owner = tp.defined_class.name || (tp.self.is_a?(Module) ? tp.self.name : tp.self.class.name)
        label = "#{owner}#{singleton ? '.' : '#'}#{tp.method_id}"
        record = lambda do |suffix, value|
          emit.call("kind" => "value", "event" => tp.event.to_s, "slot" => "#{label}:#{suffix}",
                    "file" => display_path(tp.path), "line" => tp.lineno, "value" => tagged(value))
          records += 1
        end
        if tp.event == :return
          record.call("return", tp.return_value) if opts[:returns].include?(tp.method_id.to_s) || opts[:returns].include?(label)
        else
          names = tp.parameters.map { |_, name| name }
          params.each do |method, name|
            next unless method == tp.method_id.to_s || method == label
            raise ArgumentError, "#{label} has no named parameter #{name}" unless names.include?(name)
            record.call("param:#{name}", tp.binding.local_variable_get(name))
          end
        end
      end
      begin
        trace.enable do
          opts[:sources].each { |path| load File.expand_path(path) }
          if opts[:entry]
            receiver, method = target(opts[:entry])
            receiver.__send__(method, *opts[:args])
            invocations += 1
          end
          if opts[:fuzz]
            receiver, method = target(opts[:fuzz])
            generator = Fuzzer.new(opts[:seed], opts[:depth], opts[:leaves])
            opts[:count].times do |i|
              receiver.__send__(method, *opts[:prefix], generator.sample(i))
              invocations += 1
            end
          end
        end
        raise ArgumentError, "no chosen slots were observed" if records.zero?
        emit.call("kind" => "complete", "records" => records, "invocations" => invocations)
      rescue Exception => error # Also makes partial traces from a source's exit/SystemStackError unusable.
        emit.call("kind" => "error", "class" => error.class.name, "message" => error.message)
        raise
      ensure
        trace.disable
      end
    end
    warn "recorded #{records} slot values (#{invocations} invocations) to #{display_path(opts[:output])}"
  end
end

if $PROGRAM_NAME == __FILE__
  begin
    ShapeOracle.main(ARGV)
  rescue StandardError, SystemStackError, SystemExit => error
    warn "record: #{error.class}: #{error.message}"
    exit 2
  end
end
