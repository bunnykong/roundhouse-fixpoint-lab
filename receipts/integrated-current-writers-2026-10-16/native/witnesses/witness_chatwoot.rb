require_relative 'witness_support'
gem 'activesupport', '7.2.3.1'
gem 'actionpack', '7.2.3.1'
require 'active_support/all'
require 'action_controller'
APP = File.join(INPUTS, 'chatwoot')
Time.zone = 'UTC'

# Exact source expressions; locals come from the containing method's preceding
# statements. Each observation snapshots its type before subsequent mutation.
contact = Struct.new(:email).new('person@example.test')
context = Object.new
context.define_singleton_method(:contact) { contact }
exact_expression('C134', { query: [] }, context: context)

data = [{date: '2026-01-01', hour: 1, value: 7},
        {date: '2026-01-02', hour: 2, value: 9}]
dates = data.pluck(:date).uniq.sort
result_arr = []
exact_expression('C646', { result_arr: result_arr, dates: dates })
# The block's actual source produces a missing-date nil and an Integer count.
exact_expression('C649', { result_arr: result_arr, dates: dates,
                         hour: 1, items: [data.first] })
exact_expression('C664', { result_arr: [], row: ['01:00', 7, nil] })

# Real strong-parameters conversion used by the profile controller.
path = File.join(APP, 'app/controllers/api/v1/accounts/notification_settings_controller.rb')
context = context_with_params(ActionController::Parameters.new(
  notification_settings: { selected_push_flags: ['push_conversation_assignment'] }))
install_method(context.singleton_class, path, :notification_setting_params)
call_argument(path, 28, :selected_push_flags=, ['C2428'], context: context)

path = File.join(APP, 'lib/captain/base_task_service.rb')
message = Struct.new(:content_for_llm, :incoming?).new('Hello', true)
messages = []
source_segment(path,151,151,locals:{messages:messages,message:message,content:message.content_for_llm})
# At the second eligible message, the receiver already contains the first.
exact_expression('C761',{messages:messages})

path = File.join(APP, 'app/services/csat_template_utility_rubric.rb')
load path
context = Object.new.extend(CsatTemplateUtilityRubric)
context.define_singleton_method(:sanitized_message) { 'Hello. Your support ticket is closed.' }
intro = context.send(:extracted_intro_sentence)
raise 'intro guard not met' unless intro.present?
exact_expression('C1007',{parts:[],intro:intro})

path = File.join(APP, 'app/services/data_imports/importer.rb')
context = method_context(path,[:mark_stat_group_dirty])
context.instance_variable_set(:@dirty_stat_groups,{})
context.mark_stat_group_dirty('contacts')
exact_expression('C1141',{},context:context)
# The last unconditional update adds a Symbol key irrespective of optional fields.
updates = {}
source_segment(path,315,315,locals:{updates:updates})
exact_expression('C1176',{updates:updates})

module DataImports; end
path = File.join(APP, 'app/services/data_imports/message_batch_builder.rb')
load path
context = DataImports::MessageBatchBuilder.allocate
context.instance_variable_set(:@source_conversation,{'id'=>'42','created_at'=>1,'source'=>{'body'=>'Hello'}})
exact_expression('C1204',{entries:[],source:{'body'=>'Hello'}},context:context)

path = File.join(APP,'app/services/filter_service.rb')
context = method_context(path,[:filter_operation,:values_for_ilike,:ilike_filter_string])
context.instance_variable_set(:@filter_values,{})
context.filter_operation({filter_operator:'is_present'},0)
exact_expression('C1246',{},context:context)

path = File.join(APP,'app/services/imap/base_fetch_email_service.rb')
data = Struct.new(:seqno).new(1)
entry = source_segment(path,129,129,locals:{data:data,message_id:'one@example.test'})
message_ids_with_seq = []
source_segment(path,116,116,locals:{message_ids_with_seq:message_ids_with_seq,entry:entry})
exact_expression('C1286',{message_ids_with_seq:message_ids_with_seq})
exact_expression('C1297',{message_id_with_seq:entry})

message = Struct.new(:content,:message_type).new('Hello','incoming')
path = File.join(APP,'lib/integrations/captain/processor_service.rb')
context = method_context(path,[:determine_role])
role = context.determine_role(message)
exact_expression('C1337',{previous_messages:[],message:message,role:role})

path = File.join(APP,'lib/linear/mutations.rb')
module Linear; end
load path
exact_expression('C1440',{user_params:[],user_name:'Example'},context:Linear::Mutations)

path = File.join(APP,'app/services/twilio/template_processor_service.rb')
context = method_context(path,%i[convert_media_template process_component process_media_header
                                extract_media_link process_body_parameters])
variables = {}
header = {'type'=>'header','parameters'=>[{'image'=>{'link'=>'https://example.test/image.jpg'}}]}
index = context.process_component(header,variables,1)
body = {'type'=>'body','parameters'=>[{'text'=>'Ada'},{'text'=>'Welcome'}]}
# The actual media-header predecessor has already inserted key "1".
call_argument(path,89,:process_body_parameters,['C2449'],context:context,
              locals:{component:body,content_variables:variables,parameter_index:index},index:1)
exact_expression('C1829',{content_variables:variables})

exact_expression('C1972',{missing_params:[]})

path = File.join(APP,'app/services/whatsapp/providers/base_service.rb')
context = method_context(path,[:item_description])
block = nodes_in(path).grep(Prism::BlockNode).find { |n| n.location.start_line==82 }
raise 'block not found' unless block
source_record(path,block_line:82,expression:block.location.slice)
b = context.instance_eval { binding }
b.local_variable_set(:rows,[])
proc_ = eval('proc '+block.location.slice,b,path,82)
observe_return('C2040',proc_.call({'value'=>'one','title'=>'One'}),source:path,line:82,
               expression:block.location.slice)

path = File.join(APP,'app/services/whatsapp/template_parameter_converter_service.rb')
context = method_context(path,[:convert_hash_to_body_params])
exact_expression('C2079',{legacy_params:{'1'=>'Ada'}},context:context)

path = File.join(APP,'app/services/notification/push_test_service.rb')
context = method_context(path,%i[result device_label token_tail endpoint_host])
subscription = Struct.new(:id,:subscription_attributes,:browser_push?).new(1,{'push_token'=>'abcdef'},false)
result = context.result(subscription,'fcm',:skipped,'No Firebase credentials and push relay disabled')
exact_expression('C2311',{r:result})

# Targeted follow-up outside the random sample: these exact IR identities varied
# in response-return-spine-control and are equal in all four candidate schedules.
path = File.join(APP,'lib/integrations/slack/slack_message_helper.rb')
context = method_context(path,[:resolve_slack_sender])
context.define_singleton_method(:params) { {event:{user:'U123'}} }
client = Object.new
client.define_singleton_method(:users_info) do |**_|
  {user:{profile:{email:'outside@example.test',display_name:'Example',image_192:'https://example.test/avatar.png'}}}
end
users = Object.new
users.define_singleton_method(:from_email) { |_| nil }
conversation = Struct.new(:account).new(Struct.new(:users).new(users))
context.define_singleton_method(:slack_client) { client }
context.define_singleton_method(:conversation) { conversation }
_,sender_name,sender_avatar_url = context.resolve_slack_sender
raise 'sender boundary failed' unless sender_name=='Example' && sender_avatar_url.present?
slack_sender_attrs = {}
source_segment(path,32,32,locals:{slack_sender_attrs:slack_sender_attrs,sender_name:sender_name})
exact_expression('C1431',{slack_sender_attrs:slack_sender_attrs})
source_segment(path,33,33,locals:{slack_sender_attrs:slack_sender_attrs,sender_avatar_url:sender_avatar_url})
exact_expression('C1432',{slack_sender_attrs:slack_sender_attrs})

finish('chatwoot-witnesses.json')
