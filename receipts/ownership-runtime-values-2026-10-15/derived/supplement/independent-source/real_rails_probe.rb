#!/usr/bin/env ruby
# Validate the rendering and collector doubles against installed, pinned Rails 8.1.3.
require 'json'
require 'prism'
require 'digest'
require 'action_controller'
require 'action_dispatch/testing/test_request'
abort RUBY_DESCRIPTION unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'
abort ActionPack::VERSION::STRING unless ActionPack::VERSION::STRING == '8.1.3'

INPUT_ROOT = File.expand_path(ENV.fetch('PUBLIC_MASTODON_INPUT', './inputs/mastodon'))
SOURCES = []
def install(target, file, method)
  path = File.join(INPUT_ROOT, file)
  source = File.binread(path)
  defs = []
  scan = lambda do |node|
    defs << node if node.is_a?(Prism::DefNode) && node.name == method
    node.compact_child_nodes.each { |child| scan.call(child) }
  end
  parsed = Prism.parse(source)
  raise parsed.errors.inspect unless parsed.success?
  scan.call(parsed.value)
  raise method.to_s unless defs.size == 1
  node = defs.first
  target.class_eval(node.location.slice, path, node.location.start_line)
  SOURCES << { path: path, method: method, line: node.location.start_line,
               sha256: Digest::SHA256.hexdigest(source) }
end

class RealSuspension < ActionController::Base
  prepend_view_path File.expand_path('rails-fixtures', __dir__)
end
%i[gone forbidden not_found respond_with_error].each do |method|
  install(RealSuspension, 'app/controllers/concerns/error_responses.rb', method)
end
%i[permanent_unavailability_response temporary_suspension_response
   check_account_suspension skip_temporary_suspension_response?].each do |method|
  install(RealSuspension, 'app/controllers/concerns/account_owned_concern.rb', method)
end
class RealAPI < RealSuspension; end
install(RealAPI, 'app/controllers/api/base_controller.rb', :respond_with_error)
class RealEmbeds < RealAPI; end
install(RealEmbeds, 'app/controllers/api/web/embeds_controller.rb', :show)

AccountState = Struct.new(:permanent, :suspended) do
  def permanently_unavailable? = permanent
  def suspended? = suspended
end
HiddenStatus = Struct.new(:hidden) { def hidden? = hidden }
def controller(klass, permanent: false, suspended: false, format: 'text/html')
  object = klass.new
  request = ActionDispatch::TestRequest.create
  request.set_header('HTTP_ACCEPT', format)
  object.set_request!(request)
  object.set_response!(ActionDispatch::Response.new)
  object.instance_variable_set(:@account, AccountState.new(permanent, suspended))
  object
end

results = []
def record(results, label, object, method)
  value = object.public_send(method)
  raise "#{label}: #{value.class}: #{value.inspect}" unless value.is_a?(String)
  results << { label: label, ruby_class: value.class.name, value: value,
               http_status: object.response.status, content_type: object.response.media_type }
end
record(results, 'permanent HTML; real render, renderer, Collector and response',
       controller(RealSuspension, permanent: true), :permanent_unavailability_response)
record(results, 'temporary HTML; real render, renderer, Collector and response',
       controller(RealSuspension, suspended: true), :temporary_suspension_response)
record(results, 'ActivityPub API permanent JSON; actual API override and actual JSON renderer',
       controller(RealAPI, permanent: true, format: 'application/json'), :check_account_suspension)
embeds = controller(RealEmbeds, format: 'application/json')
embeds.instance_variable_set(:@status, HiddenStatus.new(true))
record(results, 'Embeds show hidden status; actual API override and actual JSON renderer', embeds, :show)
puts JSON.pretty_generate({ condition: 'ownership-framework-witnesses-20261015', ruby: RUBY_DESCRIPTION,
  rails: ActionPack::VERSION::STRING,
  scope: 'Real Rails renderer, Collector, response and JSON encoder; account/status doubles; local error templates',
  observations: results, sources: SOURCES,
  framework_methods: {
    render: RealSuspension.instance_method(:render).source_location,
    respond_to: RealSuspension.instance_method(:respond_to).source_location,
    collector_response: ActionController::MimeResponds::Collector.instance_method(:response).source_location,
    render_to_body: RealSuspension.instance_method(:render_to_body).source_location
  } })
