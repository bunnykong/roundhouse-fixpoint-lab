ENV['WITNESS_GEMS'] = 'chatwoot-gems'
require_relative 'witness_support'
gem 'activesupport', '7.2.3.1'
gem 'actionpack', '7.2.3.1'
gem 'activerecord', '7.2.3.1'
require 'active_record'
require 'action_controller'
require 'active_support/all'
require 'tempfile'
APP = File.join(INPUTS, 'chatwoot')
CONTROLLERS = File.join(APP, 'app/controllers/api/v1/accounts')
Time.zone = 'UTC'

module Current
  def self.user = Struct.new(:id).new(7)
end
class Conversation
  def self.arel_table = Arel::Table.new(:conversations)
  def self.priorities = { 'low' => 0, 'medium' => 1, 'high' => 2, 'urgent' => 3 }
end
class Message
  def self.arel_table = Arel::Table.new(:messages)
end

def controller(file, methods, params)
  context = context_with_params(ActionController::Parameters.new(params))
  methods.each { |name| install_method(context.singleton_class, file, name) }
  context
end

# Real strong-parameters objects remain Parameters at model method entry.
path = File.join(CONTROLLERS, 'articles_controller.rb')
article_context = controller(path, %i[list_params set_current_page article_params],
                             { locale: 'en', query: 'hello', article: { title: 'Revised title' } })
search_params = call_argument(path, 14, :search, ['C094'], context: article_context)
%w[C003 C004 C005 C006 C007 C008].each { |id| exact_expression(id, { params: search_params }) }
article_context.set_current_page
call_argument(path, 17, :page, ['C091'], context: article_context)
call_argument(path, 58, :search_by_author, ['C092'])
call_argument(path, 104, :update!, ['C093'], context: article_context)

[
  ['assignment_policies_controller.rb', :assignment_policy_params, 16, { assignment_policy: { name: 'Policy' } }, 'C095'],
  ['campaigns_controller.rb', :campaign_params, 16, { campaign: { title: 'Campaign', enabled: true } }, 'C101'],
  ['custom_attribute_definitions_controller.rb', :permitted_payload, 18,
   { custom_attribute_definition: { attribute_display_name: 'Region', attribute_key: 'region' } }, 'C142'],
  ['custom_filters_controller.rb', :permitted_payload, 19, { custom_filter: { name: 'Mine', filter_type: 'conversation' } }, 'C143'],
  ['integrations/hooks_controller.rb', :permitted_params, 11, { hook: { status: 'enabled', settings: { name: 'test' } } }, 'C157'],
  ['webhooks_controller.rb', :webhook_params, 15, { webhook: { url: 'https://example.test/hook' } }, 'C178']
].each do |file, name, line, params, id|
  path = File.join(CONTROLLERS, file)
  context = controller(path, [name], params)
  call_argument(path, line, :update!, [id], context: context)
end

path = File.join(CONTROLLERS, 'contacts/notes_controller.rb')
context = controller(path, [:note_params], { note: { content: 'Note' } })
context.instance_variable_set(:@contact, Struct.new(:id).new(3))
call_argument(path, 15, :update, ['C165'], context: context)
path = File.join(CONTROLLERS, 'conversations_controller.rb')
context = controller(path, [:permitted_update_params], { priority: 'low', status: 'open' })
call_argument(path, 48, :update!, ['C117'], context: context)
call_argument(path, 176, :status=, ['C116'], context: context)

# Keep the actual nested permit schema and actual Channel EDITABLE_ATTRS constants.
module Channel; end
%w[Api Email Line Telegram Whatsapp Sms WebWidget Instagram Tiktok TwilioSms].each { |name| Channel.const_set(name, Class.new) }
%w[email sms web_widget twilio_sms].each do |name|
  path = File.join(APP, "app/models/channel/#{name}.rb")
  node = nodes_in(path).grep(Prism::ConstantWriteNode).find { |n| n.name == :EDITABLE_ATTRS }
  attrs = eval(node.value.location.slice)
  Channel.const_get(name.camelize).const_set(:EDITABLE_ATTRS, attrs)
  source_record(path, constant: 'EDITABLE_ATTRS', expression: node.value.location.slice)
end
path = File.join(CONTROLLERS, 'inboxes_controller.rb')
[
  ['email', { email: 'inbox@example.test' }, 'C105'],
  ['sms', { phone_number: '+15555550123' }, 'C108'],
  ['web_widget', { website_url: 'https://example.test' }, 'C111']
].each do |kind, attrs, id|
  context = controller(path, %i[inbox_attributes permitted_params channel_type_from_params], { channel: attrs.merge(type: kind) })
  call_argument(path, 99, :create!, [id], context: context)
end
[
  [Channel::Email::EDITABLE_ATTRS, { email: 'inbox@example.test' }, 'C106'],
  [[], { type: 'instagram' }, 'C107'],
  [[], { type: 'tiktok' }, 'C109'],
  [Channel::TwilioSms::EDITABLE_ATTRS, { account_sid: 'witness' }, 'C110'],
  [Channel::WebWidget::EDITABLE_ATTRS, { website_url: 'https://example.test' }, 'C112']
].each do |attrs, channel_params, id|
  context = controller(path, %i[inbox_attributes permitted_params], { channel: channel_params })
  call_argument(path, 131, :update!, [id], context: context, locals: { channel_attributes: attrs })
end
context = controller(path, %i[inbox_attributes permitted_params], { name: 'Revised inbox' })
inbox_params = context.permitted_params.except(:channel, :csat_config)
call_argument(path, 57, :update!, ['C154'], locals: { inbox_params: inbox_params })

# Label [] permits scalar integers. The controller does not coerce or guard them.
path = File.join(CONTROLLERS, 'conversations/labels_controller.rb')
context = controller(path, [:permitted_params], { labels: [7] })
label_caller = File.join(APP, 'app/controllers/concerns/label_concern.rb')
labels = call_argument(label_caller, 3, :update_labels, %w[C118 C159], context: context)
exact_expression('C067', { labels: labels })
exact_expression('C068', { labels: labels })
context.params = ActionController::Parameters.new({})
call_argument(label_caller, 3, :update_labels, %w[C118 C159], context: context)

path = File.join(APP, 'app/services/whatsapp/reauthorization_service.rb')
call_argument(path, 32, :business_management_token=, ['C113'])
path = File.join(CONTROLLERS, 'contacts_controller.rb')
Dir.mkdir(File.join(__dir__, 'tmp')) unless Dir.exist?(File.join(__dir__, 'tmp'))
Tempfile.create(['upload', '.csv'], File.join(__dir__, 'tmp')) do |file|
  file.write("name,email\nExample,example@example.test\n")
  file.flush
  upload = ActionDispatch::Http::UploadedFile.new(tempfile: file, filename: 'contacts.csv', type: 'text/csv')
  context = context_with_params(ActionController::Parameters.new(import_file: upload))
  call_argument(path, 39, :attach, ['C090'], context: context)
end

# Concrete SQL, query and filter arguments from their unchanged application expressions.
call_argument(File.join(APP, 'app/services/conversations/unread_counts/filtered_counter.rb'), 129, :where, ['C144'],
              context: Object.new.tap { |o| o.define_singleton_method(:user) { Struct.new(:id).new(7) } })
context = Object.new
context.instance_variable_set(:@data_import, Struct.new(:started_at).new(nil))
call_argument(File.join(APP, 'app/services/data_imports/importer.rb'), 56, :update!, ['C145'], context: context)
call_argument(File.join(APP, 'app/builders/v2/reports/inbox_label_matrix_builder.rb'), 25, :order, ['C153'])
call_argument(File.join(APP, 'app/services/conversations/unread_counts/counter.rb'), 191, :where, ['C158'])
call_argument(File.join(APP, 'app/builders/v2/reports/outgoing_messages_count_builder.rb'), 37, :joins, ['C162'])
call_argument(File.join(APP, 'app/finders/message_finder.rb'), 22, :not, ['C163'])
call_argument(File.join(APP, 'app/builders/v2/reports/bot_metrics_builder.rb'), 35, :joins, ['C175'])

context = Object.new
path = File.join(APP, 'app/services/conversations/unread_counts/filtered_counter.rb')
install_method(context.singleton_class, path, :unread_since_last_seen_condition)
node = call_argument(path, 185, :where, ['C120'], context: context)
raise unless node.is_a?(Arel::Nodes::Node)
context.instance_variable_set(:@conversation, Struct.new(:agent_last_seen_at).new(Time.utc(2026, 1, 1)))
context.define_singleton_method(:conversation) { @conversation }
call_argument(File.join(APP, 'app/services/conversations/unread_counts/refresher.rb'), 109, :where, ['C164'], context: context)

context = context_with_params(ActionController::Parameters.new(sort_order: 'asc'))
path = File.join(APP, 'app/finders/notification_finder.rb')
install_method(context.singleton_class, path, :sort_order)
call_argument(path, 14, :order, ['C166'], context: context)

# These two retain the runtime value: primitive Time and Class[Time] denote it alike.
time_context = Object.new
time_context.define_singleton_method(:created_at) { Time.current }
call_argument(File.join(APP, 'app/models/conversation.rb'), 294, :waiting_since=, ['C119'], context: time_context)

# Keep the TimeZone discrepancy explicit: it already exists in the control.
time_context.define_singleton_method(:year_range) { Time.zone.local(2026, 1, 1)..Time.zone.local(2026, 12, 31) }
call_argument(File.join(APP, 'app/builders/year_in_review_builder.rb'), 38, :group_by_day, ['C114'], context: time_context, index: 1)

finish('chatwoot-witnesses.json')
