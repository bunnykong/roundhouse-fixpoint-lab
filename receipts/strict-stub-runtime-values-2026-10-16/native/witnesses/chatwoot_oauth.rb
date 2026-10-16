#!/usr/bin/env ruby
# Source-preserving CONTRIBUTOR-style boundary witnesses for all four narrowed render arguments.
require 'rubygems'
TASK = File.expand_path(ENV.fetch('WITNESS_VENDOR'))
local_gems = File.join(TASK, 'oauth-gems')
Gem.use_paths(local_gems, [local_gems, *Gem.path])
gem 'oauth2', '2.0.22'
require_relative 'boundary_tools'
require 'oauth2'
require 'jwt'
$LOAD_PATH.unshift(File.join(TASK, 'concurrent-ruby-1.3.8/lib/concurrent-ruby'))
$LOAD_PATH.unshift(File.join(TASK, 'activesupport-7.2.3.1/lib'))
require 'active_support/concern'
require 'active_support/core_ext/object/blank'

APP = File.join(INPUTS, 'chatwoot')
CALLS = []
LIBRARY_RETURNS = []
CURRENT_PROVIDER = {}

# Finite boundary inputs only: no real account, secret, external request or Rails boot.
class GlobalConfigService
  def self.load(key, _default = nil)
    key.end_with?('SECRET') ? 'fixture-client-secret' : 'fixture-client-id'
  end
end
module Current
  Account = Struct.new(:id)
  def self.account = Account.new(7)
end
class Time
  def self.current = Time.at(1_700_000_000).utc
end
class OAuthBoundary
  def base_url = 'https://chatwoot.example.test'
  def state = 'signed-state-fixture'
  def params = { return_to: nil }
  def render(**options)
    CALLS << { provider: CURRENT_PROVIDER[:name], options: options,
               value_type: concrete_type(options), source: caller_locations(1, 1).first.to_s }
    observe(CURRENT_PROVIDER[:name] + '/render-keywords', options, Hash)
    options
  end
end

def join_types(types)
  types = types.uniq
  return { kind: 'bottom' } if types.empty?
  return types.first if types.length == 1
  { kind: 'union', variants: types }
end

def concrete_type(value)
  case value
  when Hash
    { kind: 'hash', key: join_types(value.keys.map { |v| concrete_type(v) }),
      value: join_types(value.values.map { |v| concrete_type(v) }) }
  when Array
    { kind: 'array', elem: join_types(value.map { |v| concrete_type(v) }) }
  when Symbol then { kind: 'sym' }
  when String then { kind: 'str' }
  when TrueClass, FalseClass then { kind: 'bool' }
  when NilClass then { kind: 'nil' }
  when Integer then { kind: 'int' }
  else { kind: 'class', id: value.class.name, args: [] }
  end
end

module Instagram; end
integration = File.join(APP, 'app/helpers/instagram/integration_helper.rb')
load integration
SOURCES << { path: integration, sha256: Digest::SHA256.file(integration).hexdigest,
             extraction: 'entire unchanged module' }

trace = TracePoint.new(:return) do |tp|
  next unless tp.method_id == :authorize_url && tp.path.include?('/oauth2-2.0.22/')
  LIBRARY_RETURNS << { provider: CURRENT_PROVIDER[:name], method: tp.defined_class.to_s + '#authorize_url',
                       source: tp.path, line: tp.lineno, ruby_class: tp.return_value.class.name,
                       value: tp.return_value }
end

trace.enable do
  %w[google instagram microsoft notion].each do |provider|
    CURRENT_PROVIDER[:name] = provider
    controller = Class.new(OAuthBoundary)
    concern = File.join(APP, 'app/controllers/concerns', provider + '_concern.rb')
    install_method(controller, concern, (provider + '_client').to_sym)
    if provider == 'instagram'
      install_method(controller, concern, :client_id)
      controller.include(Instagram::IntegrationHelper)
    else
      install_method(controller, concern, :scope)
    end
    action = File.join(APP, 'app/controllers/api/v1/accounts', provider, 'authorizations_controller.rb')
    install_method(controller, action, :create)
    result = controller.new.create
    raise 'expected successful authorization response' unless result.dig(:json, :success) == true
    url = result.dig(:json, :url)
    raise 'expected actual OAuth2 URL String' unless url.is_a?(String) && url.start_with?('https://')
    observe(provider + '/url', url, String)
  end
end

deps = JSON.parse(File.read(File.expand_path('../dependency-pins.json', __dir__)))
deps.fetch('gems').each do |pin|
  spec = Gem.loaded_specs[pin.fetch('name')]
  next unless spec
  raise "dependency pin mismatch: #{pin['name']}" unless spec.version.to_s == pin.fetch('version')
end
loaded = $LOADED_FEATURES.select { |p| p.start_with?(TASK) }
puts JSON.pretty_generate({
  condition: 'strict-stub-runtime-witnesses-20261016-chatwoot-cruby407', ruby: RUBY_DESCRIPTION,
  app_pin: '9f920b549c14491a4e587687a3eed5d21c6ccc7d',
  scope: 'Unmodified create/client/token bodies; actual locked OAuth2 URL builder; render argument capture; finite configuration/account/clock inputs.',
  sources: SOURCES, observations: OBSERVATIONS, render_calls: CALLS, library_returns: LIBRARY_RETURNS,
  loaded_gems: Gem.loaded_specs.transform_values { |s| { version: s.version.to_s, path: s.full_gem_path } },
  loaded_sources: loaded.map { |p| { path: p, sha256: Digest::SHA256.file(p).hexdigest } }
})
