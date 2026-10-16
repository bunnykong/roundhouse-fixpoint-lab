ENV['WITNESS_GEMS'] = 'mastodon-gems'
require_relative 'witness_support'
gem 'activerecord', '8.1.3'
gem 'sqlite3', '2.10.0'
require 'active_record'
require 'active_support/all'
APP = File.join(INPUTS, 'mastodon')

call_argument(File.join(APP, 'app/models/export.rb'), 34, :reorder, ['M192'])
call_argument(File.join(APP, 'app/models/export.rb'), 14, :reorder, ['M207'])
call_argument(File.join(APP, 'app/services/notify_of_collection_update_service.rb'), 7, :includes, ['M211'])
call_argument(File.join(APP, 'app/lib/account_reach_finder.rb'), 44, :select, ['M213'])
call_argument(File.join(APP, 'app/lib/account_reach_finder.rb'), 23, :select, ['M225'])
call_argument(File.join(APP, 'app/services/delete_account_service.rb'), 138, :where, ['M217'])
context = Object.new
context.define_singleton_method(:reported_status_ids) { [1] }
call_argument(File.join(APP, 'app/services/delete_account_service.rb'), 179, :not, ['M223'], context: context)

# The controller's scalar-permit contract allows the String; Ruby's setter receives
# it before ActiveRecord's Boolean column caster handles storage.
context.instance_variable_set(:@options, { poll: { multiple: 'true' } })
call_argument(File.join(APP, 'app/services/update_status_service.rb'), 98, :multiple=, ['M222'], context: context)

# An ordinary same-origin remote featured collection supplies String and Integer
# attributes. All attribute construction and URL/summary helpers are unchanged.
class Collection; end
path = File.join(APP, 'app/models/collection.rb')
nodes_in(path).grep(Prism::ConstantWriteNode).each do |node|
  next unless %i[NAME_LENGTH_HARD_LIMIT DESCRIPTION_LENGTH_HARD_LIMIT].include?(node.name)
  Collection.const_set(node.name, eval(node.value.location.slice))
end
source_record(path, constants: [Collection::NAME_LENGTH_HARD_LIMIT, Collection::DESCRIPTION_LENGTH_HARD_LIMIT])
path = File.join(APP, 'app/services/activitypub/process_featured_collection_service.rb')
%i[collection_attributes truncated_summary language url].each { |name| install_method(context.singleton_class, path, name) }
install_method(context.singleton_class, File.join(APP, 'app/helpers/json_ld_helper.rb'), :url_to_href)
context.instance_variable_set(:@json, { 'id' => 'https://example.test/collection', 'name' => 'Example',
                                      'summary' => 'A description', 'sensitive' => false,
                                      'discoverable' => true, 'totalItems' => 1 })
call_argument(path, 21, :update!, ['M209'], context: context)

# Actual AR 8.1.3 through-association object, using the application's unchanged
# relationship declarations and a finite SQLite database boundary.
ActiveRecord::Base.establish_connection(adapter: 'sqlite3', database: ':memory:')
ActiveRecord::Schema.verbose = false
ActiveRecord::Schema.define do
  create_table(:accounts)
  create_table(:follows) { |t| t.integer :account_id; t.integer :target_account_id }
end
class Account < ActiveRecord::Base; end
class Follow < ActiveRecord::Base
  belongs_to :account
  belongs_to :target_account, class_name: 'Account'
end
path = File.join(APP, 'app/models/concerns/account/interactions.rb')
nodes = nodes_in(path).grep(Prism::CallNode)
[nodes.find { |n| n.name == :with_options && n.message_loc&.start_line == 10 },
 nodes.find { |n| n.name == :has_many && n.message_loc&.start_line == 16 }].each do |node|
  raise 'missing association declaration' unless node
  Account.class_eval(node.location.slice, path, node.location.start_line)
  source_record(path, expression: node.location.slice, line: node.location.start_line)
end
account = Account.create!
follower = Account.create!
Follow.create!(account: follower, target_account: account)
class Quote
  attr_reader :account
  def initialize(account) = @account = account
end
context.instance_variable_set(:@quote, Quote.new(account))
value = exact_expression('M097', {}, context: context)
raise 'the witness must actually exercise a collection proxy' if value.is_a?(Array)
raise 'bad association fixture' unless value.to_a == [follower]
finish('mastodon-witnesses.json')
