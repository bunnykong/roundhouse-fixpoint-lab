#!/usr/bin/env ruby
# Tiny, source-preserving boundary witnesses; not a full Rails application boot.
require 'json'
require 'prism'
require 'digest'
require 'erb'
abort "CRuby 4.0.7 required: #{RUBY_DESCRIPTION}" unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'

HERE = File.expand_path(__dir__)
INPUTS = File.expand_path('../../ownership-generalization/inputs', HERE)
SOURCES = []
OBSERVATIONS = []

def install_method(target, path, name)
  source = File.binread(path)
  ast = Prism.parse(source)
  raise ast.errors.inspect unless ast.success?
  found = []
  walk = ->(node) do
    return unless node
    found << node if node.is_a?(Prism::DefNode) && node.name.to_s == name.to_s
    node.compact_child_nodes.each { |child| walk.call(child) }
  end
  walk.call(ast.value)
  raise "Expected one #{name} in #{path}, got #{found.size}" unless found.size == 1
  n = found.first
  target.module_eval(n.location.slice, path, n.location.start_line)
  SOURCES << { path: path, sha256: Digest::SHA256.hexdigest(source), method: name,
               start: n.location.start_offset, end: n.location.end_offset, line: n.location.start_line }
end

def observe(label, value, expected)
  raise "#{label}: expected #{expected}, got #{value.inspect}" unless value.is_a?(expected)
  OBSERVATIONS << { label: label, value: value, ruby_class: value.class.name }
end

# Forem's actual module methods and controller callbacks, with the version of
# rendering/redirecting pinned by Forem's Gemfile.lock. Collaborators are finite
# test doubles; neither callback nor the methods' Ruby return behavior is replaced.
module ActiveRecord
  class Rollback < StandardError; end
  class Base
    def self.transaction
      yield
    rescue Rollback
      nil
    end
  end
end
module Credits
  class Buyer
    def self.call(**) = nil
  end
end
class Organization; end
class Time
  def self.current = Time.at(0)
end
ERB::Util.define_singleton_method(:unwrapped_html_escape) { |s| ERB::Util.html_escape(s) }

CreditBag = Struct.new(:unspent)
Person = Struct.new(:credits, :organizations)
class ListingDouble
  attr_accessor :published, :bumped_at, :originally_published_at, :cached_tag_list, :author
  def initialize(saved)
    @saved = saved
    @author = Person.new(CreditBag.new([:credit, :credit]), [])
  end
  def save = @saved
  def errors = ['example validation error']
end
class TrackingDouble
  def track_limit_by_action(*) = nil
end

module ListingsMethods; end
%w[create_draft create_listing first_publish].each do |method|
  install_method(ListingsMethods, File.join(INPUTS, 'forem/app/controllers/concerns/listings_toolkit.rb'), method)
end

class BoundaryController
  attr_accessor :response_body, :status, :location
  def initialize(saved)
    @listing = ListingDouble.new(saved)
    @user = Person.new(CreditBag.new([:credit]), [])
  end
  def current_user = @user
  def listing_params = { tag_list: 'ruby' }
  def rate_limiter = TrackingDouble.new
  def clear_listings_cache = nil
  def listings_path = '/listings'
  def credits_path = '/credits'
  def request = nil
  def response = self
  def _extract_redirect_to_status(*) = 302
  def _compute_redirect_to_location(_, target) = target
  def _normalize_render(*) = {}
  def render_to_body(*) = '<rendered public fixture>'
  def rendered_format = :html
  def _set_rendered_content_type(*) = nil
  def _set_html_content_type = nil
  def _set_vary_header = nil
  include ListingsMethods
end
install_method(BoundaryController, File.join(HERE, 'rails-6.1.4.1/rendering.rb'), :render)
install_method(BoundaryController, File.join(HERE, 'rails-6.1.4.1/redirecting.rb'), :redirect_to)

%w[ListingsController Api::V0::ListingsController].each do |name|
  host = Class.new(BoundaryController)
  path = name.start_with?('Api') ? 'api/v0/listings_controller.rb' : 'listings_controller.rb'
  %w[process_successful_draft process_unsuccessful_draft process_successful_creation
     process_unsuccessful_creation process_no_credit_left].each do |method|
    install_method(host, File.join(INPUTS, 'forem/app/controllers', path), method)
  end
  [true, false].each do |saved|
    { create_draft: [], create_listing: [nil, 1], first_publish: [1] }.each do |method, args|
      object = host.new(saved)
      observe("forem/#{name}##{method}/save=#{saved}", object.public_send(method, *args), String)
    end
  end
end

# Mastodon's source method: Ruby Hash lookup, case discrimination and fallthrough.
module CollectionMethods; end
install_method(CollectionMethods, File.join(INPUTS, 'mastodon/app/helpers/json_ld_helper.rb'), :collection_page_items)
collector = Object.new.extend(CollectionMethods)
[
  ['Collection', { 'items' => ['item-a'] }, Array],
  ['CollectionPage', { 'items' => [{ 'id' => 'item-b' }] }, Array],
  ['OrderedCollection', { 'orderedItems' => ['item-c'] }, Array],
  ['OrderedCollectionPage', { 'orderedItems' => [{ 'id' => 'item-d' }] }, Array],
  ['Collection', {}, NilClass],
  ['Unknown', {}, NilClass]
].each_with_index do |(kind, fields, expected), index|
  value = collector.collection_page_items(fields.merge('type' => kind))
  observe("mastodon/collection_page_items/#{kind}/#{index}", value, expected)
end

# The helper has no runtime schema guard on the language-map fallback.
%w[first_of_value first_lang_string].each do |method|
  install_method(CollectionMethods, File.join(INPUTS, 'mastodon/app/helpers/json_ld_helper.rb'), method)
end
observe('mastodon/first_lang_string/language-map-integer',
        collector.first_lang_string({ 'nameMap' => { 'en' => 7 } }, 'name'), Integer)
observe('mastodon/first_lang_string/string-branch', collector.first_lang_string({ 'name' => 'hello' }, 'name'), String)
observe('mastodon/first_of_value/empty-array', collector.first_of_value([]), NilClass)
install_method(CollectionMethods, File.join(INPUTS, 'mastodon/app/helpers/json_ld_helper.rb'), :url_to_href)
observe('mastodon/url_to_href/empty-array-find', collector.url_to_href([]), NilClass)
observe('mastodon/url_to_href/string-array', collector.url_to_href(['https://example.test/']), String)
observe('mastodon/url_to_href/link-without-href', collector.url_to_href([{}]), NilClass)

module WebauthnMethods; end
install_method(WebauthnMethods, File.join(INPUTS,
  'mastodon/app/controllers/concerns/auth/two_factor_authentication_concern.rb'), :webauthn_enabled?)
auth = Object.new.extend(WebauthnMethods)
observe('mastodon/webauthn_enabled?/unset-ivar', auth.webauthn_enabled?, NilClass)
auth.instance_variable_set(:@webauthn_enabled, true)
observe('mastodon/webauthn_enabled?/set-true', auth.webauthn_enabled?, TrueClass)
auth.instance_variable_set(:@webauthn_enabled, false)
observe('mastodon/webauthn_enabled?/set-false', auth.webauthn_enabled?, FalseClass)

class Integer
  def minutes = self * 60
end
class SuspensionController < BoundaryController
  class Collector
    attr_reader :response
    def initialize(*) = nil
    def any(&block) = (@response = block)
    def json(&) = nil
    def negotiate_format(*) = :html
    def any_response? = true
  end
  Request = Struct.new(:variant)
  AccountState = Struct.new(:permanent, :suspended) do
    def permanently_unavailable? = permanent
    def suspended? = suspended
  end
  def initialize(permanent, suspended)
    super(true)
    @account = AccountState.new(permanent,suspended)
  end
  def request = Request.new(nil)
  def media_type = nil
  def _process_format(*) = nil
  def expires_in(*) = nil
end
install_method(SuspensionController, File.join(HERE, 'rails-8.1.3/rendering.rb'), :render)
install_method(SuspensionController, File.join(HERE, 'rails-8.1.3/mime_responds.rb'), :respond_to)
%w[gone forbidden respond_with_error].each do |method|
  install_method(SuspensionController, File.join(INPUTS, 'mastodon/app/controllers/concerns/error_responses.rb'), method)
end
%w[permanent_unavailability_response temporary_suspension_response
   check_account_suspension skip_temporary_suspension_response?].each do |method|
  install_method(SuspensionController, File.join(INPUTS, 'mastodon/app/controllers/concerns/account_owned_concern.rb'), method)
end
observe('mastodon/permanent_unavailability_response/html',
        SuspensionController.new(true,false).permanent_unavailability_response, String)
observe('mastodon/temporary_suspension_response/html',
        SuspensionController.new(false,true).temporary_suspension_response, String)
observe('mastodon/check_account_suspension/permanent',
        SuspensionController.new(true,false).check_account_suspension, String)
observe('mastodon/check_account_suspension/temporary',
        SuspensionController.new(false,true).check_account_suspension, String)
observe('mastodon/check_account_suspension/active',
        SuspensionController.new(false,false).check_account_suspension, NilClass)

# These context-specific values agree with the variant under the stated collaborator contract.
module Admin
  class ActionLog; end
end
class ActionLogsDouble
  def create(**) = Admin::ActionLog.new
end
class Account
  def action_logs = ActionLogsDouble.new
end
class AccountController
  attr_reader :current_user
  def initialize(user) = (@current_user = user)
end
install_method(AccountController, File.join(INPUTS, 'mastodon/app/controllers/application_controller.rb'), :current_account)
install_method(AccountController, File.join(INPUTS, 'mastodon/app/controllers/concerns/authorization.rb'), :pundit_user)
install_method(AccountController, File.join(INPUTS, 'mastodon/app/controllers/concerns/accountable_concern.rb'), :log_action)
observe('mastodon/pundit_user/no-current-user', AccountController.new(nil).pundit_user, NilClass)
account_controller = AccountController.new(Struct.new(:account).new(Account.new))
observe('mastodon/pundit_user/account', account_controller.pundit_user, Account)
log = account_controller.log_action(:example, nil)
observe('mastodon/log_action/create-contract', log, Admin::ActionLog)

puts JSON.pretty_generate({
  condition: 'ownership-ruby-boundary-witnesses-20261015', ruby: RUBY_DESCRIPTION,
  scope: 'Unmodified selected Ruby methods; finite boundary doubles; no full Rails boot or coverage claim',
  collaborators: ['Forem model persistence/credits/transaction/clock doubles',
                  'render_to_body returns a String; response/location accessors and URL/status normalization doubles',
                  'Pinned Rails 6.1.4.1 render and redirect_to bodies execute unchanged',
                  'Mastodon collection_page_items and first_lang_string execute unchanged with literal Hash inputs',
                  'Rails 8.1.3 render/respond_to execute unchanged; finite HTML format collector and renderer doubles',
                  'Account current_user and action_logs.create collaborators return explicit fixture objects',
                  'Unset webauthn ivar is a Ruby boundary case; no claim it occurs after prompt_for_two_factor'],
  sources: SOURCES, observations: OBSERVATIONS
})
