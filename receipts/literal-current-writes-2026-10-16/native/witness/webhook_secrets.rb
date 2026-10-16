# literal-transfer runtime witness: Chatwoot MetaTokenVerifyConcern#channel_meta_app_secrets.
#
# Executes the pinned source of `channel_meta_app_secrets` and
# `provider_config_meta_app_secrets` verbatim (extracted from the input tree),
# with minimal ActiveSupport shims, on stub channels. Records the runtime shape
# of the `secrets` literal at method exit (TracePoint :return binding) and of
# the return value. No Rails, no database: a boundary witness, like #964's.
#
# Usage: ruby webhook_secrets.rb INPUT_ROOT OUT.json
require 'json'
require 'digest'

root, out = ARGV
abort 'usage: webhook_secrets.rb INPUT_ROOT OUT.json' unless root && out
rel = 'app/controllers/concerns/meta_token_verify_concern.rb'
path = File.join(root, rel)
text = File.read(path)
lines = text.lines

def extract_method(lines, name)
  start = lines.index { |l| l =~ /\A(\s*)def #{Regexp.escape(name)}\b/ } or raise "no def #{name}"
  indent = lines[start][/\A\s*/]
  stop = (start + 1...lines.size).find { |i| lines[i] =~ /\A#{indent}end\b/ } or raise "no end for #{name}"
  lines[start..stop].join
end

const = lines.find { |l| l =~ /CHANNEL_APP_SECRET_KEYS\s*=/ } or raise 'no CHANNEL_APP_SECRET_KEYS'
methods = %w[channel_meta_app_secrets provider_config_meta_app_secrets].map { |m| extract_method(lines, m) }

# Shims with ActiveSupport semantics for the values these methods see.
class Object
  def blank? = respond_to?(:empty?) ? !!empty? : !self
  def present? = !blank?
  def presence = present? ? self : nil
end
class String
  def blank? = strip.empty?
end
class Array
  def compact_blank = reject(&:blank?)
end
class IndifferentHash < Hash
  def [](k) = super(k.is_a?(Symbol) ? k.to_s : k)
end
class Hash
  def with_indifferent_access = IndifferentHash.new.merge!(transform_keys { |k| k.is_a?(Symbol) ? k.to_s : k })
end

class Witness; end
Witness.class_eval(const)
methods.each { |m| Witness.class_eval(m) }
Witness.send(:public, :channel_meta_app_secrets, :provider_config_meta_app_secrets)

def shape(v)
  case v
  when Array then { 'class' => 'Array', 'elems' => v.map { |x| shape(x) }.uniq }
  when Hash then { 'class' => 'Hash', 'pairs' => v.map { |k, x| [shape(k), shape(x)] }.uniq }
  else { 'class' => v.class.name, 'ancestors' => v.class.ancestors.map(&:to_s) }
  end
end

Chan = Struct.new(:app_secret, :provider_config, keyword_init: true)
OnlyConfig = Struct.new(:provider_config)
Bare = Class.new

cases = {
  'nil channel' => nil,
  'app_secret and provider_config' => Chan.new(app_secret: 's1', provider_config: { 'app_secret' => 'stratum2', 'client_secret' => '', 'api_secret' => 'research condition' }),
  'nil app_secret' => Chan.new(app_secret: nil, provider_config: { 'app_secret_key' => 'k1' }),
  'provider_config only' => OnlyConfig.new({ 'client_secret' => 'c1' }),
  'neither' => Bare.new
}

w = Witness.new
results = cases.map do |label, channel|
  at_exit = nil
  tp = TracePoint.new(:return) do |t|
    if t.method_id == :channel_meta_app_secrets && t.binding.local_variable_defined?(:secrets)
      at_exit = t.binding.local_variable_get(:secrets).dup
    end
  end
  ret = tp.enable { w.channel_meta_app_secrets(channel) }
  { 'case' => label, 'return_value' => shape(ret), 'literal_at_exit' => at_exit && shape(at_exit) }
end

# A probe is the list of distinct runtime shapes observed at one program point;
# a type admits the probe when it admits every shape in it.
def probe(shapes) = shapes.compact.uniq

doc = {
  'witness' => 'chatwoot-webhook-channel-meta-app-secrets',
  'ruby' => RUBY_DESCRIPTION,
  'source' => rel,
  'source_sha256' => Digest::SHA256.hexdigest(text),
  'declarations' => %w[Webhooks::InstagramController#channel_meta_app_secrets Webhooks::WhatsappController#channel_meta_app_secrets],
  'probes' => {
    'return_value' => probe(results.map { |r| r['return_value'] }),
    'literal_at_exit' => probe(results.map { |r| r['literal_at_exit'] })
  },
  'cases' => results
}
File.write(out, JSON.pretty_generate(doc) + "\n")
puts JSON.generate(doc['probes'].transform_values { |v| v.map { |x| [x['class'], (x['elems'] || []).map { |e| e['class'] }] } })
