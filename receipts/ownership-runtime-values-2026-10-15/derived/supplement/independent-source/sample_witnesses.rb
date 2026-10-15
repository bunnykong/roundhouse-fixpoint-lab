#!/usr/bin/env ruby
# Additional finite boundary probes; original Ruby method bodies remain unchanged.
require 'stringio'
original = File.expand_path(ENV.fetch('OWNERSHIP_WITNESSES', '../../../native/ownership.rb'), __dir__)
saved_stdout = $stdout
begin
  $stdout = StringIO.new
  load original
ensure
  $stdout = saved_stdout
end

SAMPLES = []
def sample(id, value, expected, route, overall: nil)
  raise "#{id}: #{value.inspect}" unless value.is_a?(expected)
  SAMPLES << { row_id: id, value: value, ruby_class: value.class.name, route: route,
               whole_method_return: overall }
end

# These extra collaborators make the original outer create method executable.
# Chosen state: valid listing, no organization, enough personal credits, save succeeds.
class NilClass
  def present? = false
end
class Organization
  def self.find_by(**) = nil
end
class Person
  def id = 1
  def enough_credits?(cost) = credits.unspent.size >= cost
end
class Listing < ListingDouble
  attr_accessor :user_id
  def initialize(_) = super(true)
  def organization_id = nil
  def valid? = true
  def cost = 1
end
class SampleForemBase < BoundaryController
  attr_accessor :draft
  def listing_params = { tag_list: 'ruby', action: draft ? 'draft' : 'publish' }
  def rate_limit? = false
end
install_method(SampleForemBase, File.join(INPUTS, 'forem/app/controllers/concerns/listings_toolkit.rb'), :create)
class SampleForemAPI < SampleForemBase; end
class SampleForemWeb < SampleForemBase; end
{ SampleForemAPI => 'api/v0/listings_controller.rb', SampleForemWeb => 'listings_controller.rb' }.each do |host, path|
  %w[process_successful_draft process_unsuccessful_draft process_successful_creation
     process_unsuccessful_creation process_no_credit_left].each do |method|
    install_method(host, File.join(INPUTS, 'forem/app/controllers', path), method)
  end
end
sample('F0001', SampleForemAPI.new(true).create, String,
       'Exact create body -> personal-credit create_listing -> API render; terminal Seq value')
sample('F0066', SampleForemWeb.new(true).create, String,
       'Exact create body -> elsif current_user.enough_credits? -> create_listing -> redirect; terminal If value')
draft = SampleForemAPI.new(true)
draft.draft = true
draft_call_value = nil
trace = TracePoint.new(:return) do |event|
  draft_call_value = event.return_value if event.self.equal?(draft) && event.method_id == :create_draft
end
whole_return = trace.enable { draft.create }
raise 'Bare return in create should return nil' unless whole_return.nil?
sample('F0102', draft_call_value, String,
       'TracePoint captures create_draft Send inside exact create; subsequent bare return returns nil',
       overall: whole_return)
sample('F0216', SampleForemWeb.new(true).first_publish(1), String,
       'Exact first_publish -> author credit branch -> create_listing -> redirect')

sample('M0004', SuspensionController.new(true, false).check_account_suspension, String,
       'Exact check_account_suspension -> permanent branch -> gone -> ErrorResponses HTML block')
sample('M1740', SuspensionController.new(true, false).permanent_unavailability_response, String,
       'Exact permanent_unavailability_response -> gone -> ErrorResponses HTML block')
sample('M2077', SuspensionController.new(false, true).temporary_suspension_response, String,
       'Exact temporary_suspension_response -> forbidden -> ErrorResponses HTML block')

# ActivityPub::BaseController and Api::Web::EmbedsController inherit this override.
# The original witness only exercises ErrorResponses#respond_with_error.
module Rack
  module Utils
    HTTP_STATUS_CODES = { 403 => 'Forbidden', 404 => 'Not Found', 410 => 'Gone' }.freeze
  end
end
class SampleMastodonAPI < SuspensionController; end
install_method(SampleMastodonAPI, File.join(INPUTS, 'mastodon/app/controllers/api/base_controller.rb'),
               :respond_with_error)
sample('M1113', SampleMastodonAPI.new(true, false).check_account_suspension, String,
       'Exact suspension body -> gone -> actual Api::BaseController#respond_with_error -> JSON render')
class SampleEmbeds < SampleMastodonAPI; end
install_method(SampleEmbeds, File.join(INPUTS, 'mastodon/app/controllers/concerns/error_responses.rb'), :not_found)
install_method(SampleEmbeds, File.join(INPUTS, 'mastodon/app/controllers/api/web/embeds_controller.rb'), :show)
hidden_status = Struct.new(:hidden) { def hidden? = hidden }.new(true)
embeds = SampleEmbeds.new(false, false)
embeds.instance_variable_set(:@status, hidden_status)
sample('M1973', embeds.show, String,
       'Exact show -> hidden status -> not_found -> actual API respond_with_error -> JSON render')

sample('M1788', Object.new.extend(CollectionMethods).first_lang_string({ 'nameMap' => { 'en' => 7 } }, 'name'),
       Integer, 'Exact JsonLdHelper#first_lang_string with literal Hash; no collaborators')
raise "Expected ten distinct rows" unless SAMPLES.size == 10 && SAMPLES.map { |r| r[:row_id] }.uniq.size == 10
puts JSON.pretty_generate({ condition: 'ownership-sampled-witnesses-20261015', ruby: RUBY_DESCRIPTION,
  scope: 'Finite boundary probes using exact source methods; no full Forem or Mastodon boot',
  samples: SAMPLES.sort_by { |r| r[:row_id] }, sources: SOURCES.uniq })
