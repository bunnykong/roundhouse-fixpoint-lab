# CRuby witness for Forem's @missing_configs controller binding, the row the first projection dropped.
#
# Loads the unchanged VerifySetupCompleted concern from the pinned Forem source (APPS, default corpus/apps)
# with small stand-ins for ActiveSupport::Concern, Settings, flash and the view helpers. No Rails boot.
# The projected type is `Array[Symbol] | nil`; it admits each value printed here.
require 'digest'
require 'json'

abort "CRuby 4.0.7 required; this is #{RUBY_DESCRIPTION}" unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'

apps = ENV.fetch('APPS', File.expand_path('../../corpus/apps', __dir__))
file = File.join(apps, 'forem', 'app/controllers/concerns/verify_setup_completed.rb')
abort "missing #{file}; set APPS to a directory of pinned app checkouts" unless File.file?(file)
unless Digest::SHA256.file(file).hexdigest == '7c9731e0e095fc3804af6a285fbd573b8d76f2db3ec1194818ebef6fc4695fee'
  abort "#{file}: unexpected SHA-256"
end

module ActiveSupport
  module Concern # stand-in: run the `included do` block in the includer, as Rails does
    def included(base = nil, &block)
      return @included_block = block unless base

      super(base)
      base.class_eval(&@included_block) if @included_block
    end
  end
end

MISSING = []
module Settings
  module Mandatory; def self.missing = MISSING.dup; end
  module General; def self.waiting_on_first_user = false; end
end
class NilClass; def present? = false; end
class String; def present? = !empty?; end
class Array; def to_sentence = join(', '); end

load file

class WitnessController
  FILTERS = []
  def self.before_action(name, **opts) = FILTERS << [name, opts]
  include VerifySetupCompleted
  attr_writer :flash

  def flash = (@flash ||= {})
  def request = Struct.new(:env).new({ 'PATH_INFO' => '/articles' })
  def admin_config_path = '/admin/config'
  def helpers = self
  def tag = self
  def a(*) = 'link'
  def safe_join(parts) = parts.join
end

def run(missing, flash: {})
  MISSING.replace(missing)
  controller = WitnessController.new
  controller.flash = flash
  controller.send(:verify_setup_completed)
  set = controller.instance_variable_defined?(:@missing_configs)
  { set: set, value: set ? controller.instance_variable_get(:@missing_configs).inspect : 'unset' }
end

cases = {
  incomplete_setup: run(%i[secret_key_base community_name]),
  complete_setup: run([]),
  flash_already_set: run([:secret_key_base], flash: { global_notice: 'x' }),
}
puts JSON.pretty_generate(ruby: RUBY_DESCRIPTION, filter: WitnessController::FILTERS.map { |n, o| [n, o] }, cases: cases)
