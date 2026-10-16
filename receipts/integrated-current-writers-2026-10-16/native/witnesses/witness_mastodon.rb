ENV['TMPDIR'] = ENV.fetch('WITNESS_TMPDIR')
Dir.mkdir(ENV['TMPDIR']) unless Dir.exist?(ENV['TMPDIR'])
require_relative 'witness_support'
gem 'activerecord', '8.1.3'
gem 'sqlite3', '2.10.0'
require 'active_record'
require 'active_support/all'
require 'ipaddr'
require 'tempfile'
APP = File.join(INPUTS,'mastodon')

# Load the actual settings DSL and complete definitions. Defaults are lazy;
# no application boot or external service is necessary to enumerate keys.
class UserSettings; end
%w[dsl setting namespace glue].each do |file|
  path=File.join(APP,"app/models/user_settings/#{file}.rb")
  load path
  source_record(path)
end
path=File.join(APP,'app/models/user_settings.rb')
load path
source_record(path)
%w[M246 M2047 M2050].each { |id| exact_expression(id) }
path=File.join(APP,'app/models/user_settings/dsl.rb')
block=nodes_in(path).grep(Prism::BlockNode).find { |n| n.location.start_line==20 }
raise 'namespace block missing' unless block
source_record(path,expression:block.location.slice,line:20)
namespace=UserSettings::Namespace.new(:audit).configure { setting :enabled, default: true }
binding_=UserSettings.instance_eval { binding }
proc_=eval('proc '+block.location.slice,binding_,path,20)
observe_return('M2307',proc_.call(namespace),source:path,line:20,expression:block.location.slice)

# Actual ActiveRecord queries over finite SQLite tables, mirroring only the
# columns used by the unchanged methods. No application validations are claimed.
ActiveRecord::Base.establish_connection(adapter:'sqlite3',database:':memory:')
ActiveRecord::Schema.verbose=false
ActiveRecord::Schema.define do
  create_table(:accounts) { |t| t.string :username; t.string :domain }
  create_table(:follows) do |t|
    t.integer :account_id; t.integer :target_account_id
    t.boolean :show_reblogs, default:true; t.boolean :notify, default:false
    t.json :languages, default:[]
  end
  create_table(:media_attachments) { |t| t.string :remote_url; t.boolean :skip_download, default:false }
end
class Account < ActiveRecord::Base; end
class Follow < ActiveRecord::Base; end
class MediaAttachment < ActiveRecord::Base; end
path=File.join(APP,'app/models/account.rb')
%i[acct local?].each { |name| install_method(Account,path,name) }
install_method(Account.singleton_class,File.join(APP,'app/models/concerns/account/mappings.rb'),:following_map)
viewer=Account.create!(username:'viewer')
target=Account.create!(username:'alice')
Follow.create!(account_id:viewer.id,target_account_id:target.id)
following=Account.following_map([target.id],viewer.id)
path=File.join(APP,'app/presenters/account_relationships_presenter.rb')
load path
source_record(path,line:4,explanation:'actual attr_reader; initialize merges cached map with following_map')
presenter=AccountRelationshipsPresenter.allocate
presenter.instance_variable_set(:@following,following)
observe('actual-following-reader',presenter.following,['M355'],source:path,line:4,
        boundary:'Actual following_map query; cache is empty; getter is unchanged')

# A real remote featured URL is forwarded by the account processing job payload.
path=File.join(APP,'app/services/activitypub/process_account_service.rb')
context=Object.new
context.instance_variable_set(:@json,{'featured'=>'https://remote.example.test/featured','featuredTags'=>nil})
context.instance_variable_set(:@options,{})
options=call_argument(path,217,:perform_async,[],context:context,index:1)
path=File.join(APP,'app/workers/activitypub/synchronize_featured_collection_worker.rb')
options=source_segment(path,9,9,locals:{options:options})
exact_expression('M586',{options:options})

module ActivityPub
  class TagManager; end
end
path=File.join(APP,'app/lib/activitypub/tag_manager.rb')
node=nodes_in(path).grep(Prism::ConstantWriteNode).find { |n| n.name==:COLLECTIONS }
ActivityPub::TagManager.const_set(:COLLECTIONS,eval(node.value.location.slice))
source_record(path,expression:node.location.slice,line:node.location.start_line)
exact_expression('M664',{approved_uris:[]})

# Both normal-download and rescue positions read the same persisted AR record.
# The only substituted boundary is a network download that raises the app's
# declared UnexpectedResponseError. No HTTP request or worker enqueue is made.
module Mastodon
  class Error < StandardError; end
end
path=File.join(APP,'lib/exceptions.rb')
node=nodes_in(path).grep(Prism::ClassNode).find { |n| n.constant_path.location.slice=='UnexpectedResponseError' }
Mastodon.module_eval(node.location.slice,path,node.location.start_line)
source_record(path,expression:node.location.slice,line:node.location.start_line)
attachment=MediaAttachment.create!(remote_url:'https://remote.example.test/image.png')
raise 'changed URL needed' unless attachment.remote_url_previously_changed?
Mastodon::HTTP_CONNECTION_ERRORS=[] # other network exception classes cannot affect this witness
class ActivityPub::ProcessStatusUpdateService; end
path=File.join(APP,'app/services/activitypub/process_status_update_service.rb')
delay=nodes_in(path).grep(Prism::ConstantWriteNode).find { |n| n.name==:PROCESSING_DELAY }
ActivityPub::ProcessStatusUpdateService.class_eval(delay.location.slice,path,delay.location.start_line)
source_record(path,expression:delay.location.slice,line:delay.location.start_line)
install_method(ActivityPub::ProcessStatusUpdateService,path,:download_media_files!)
class RedownloadMediaWorker
  class << self
    attr_accessor :captured
    def perform_in(delay,id)
      self.captured=[delay,id] # queue boundary only; never enqueue a job
    end
  end
end
attachment.define_singleton_method(:download_file!) { raise Mastodon::UnexpectedResponseError }
service=ActivityPub::ProcessStatusUpdateService.new
service.instance_variable_set(:@next_media_attachments,[attachment])
service.instance_variable_set(:@status,Struct.new(:media_attachments).new(MediaAttachment.all))
seen=[]
trace=TracePoint.new(:line) do |tp|
  next unless tp.path==path && [130,134].include?(tp.lineno)
  id=tp.lineno==130 ? 'M703' : 'M707'
  seen << id
  observe('actual-download-method-'+id,tp.binding.local_variable_get(:media_attachment),[id],
          source:path,line:tp.lineno,
          boundary:'unchanged full download_media_files!; download raises actual app exception; queue sink records only')
end
trace.enable { service.send(:download_media_files!) }
raise 'both real method positions must execute' unless seen==%w[M703 M707]
raise 'rescue did not use the persisted attachment' unless RedownloadMediaWorker.captured.last==attachment.id

path=File.join(APP,'app/helpers/json_ld_helper.rb')
context=method_context(path,[:equals_or_includes?])
context.instance_variable_set(:@raw_mentions,[])
context.instance_variable_set(:@raw_emojis,[])
context.instance_variable_set(:@raw_tagged_objects,[])
exact_expression('M745',{tag:{'type'=>'Mention','href'=>'https://remote.example.test/@alice'}},context:context)
exact_expression('M951',{links:[],next_path:'https://example.test/api/v1/statuses?max_id=2'})

old_preset=ENV.delete('ES_PRESET')
begin
  exact_expression('M1172',{base_options:{}})
ensure
  ENV['ES_PRESET']=old_preset if old_preset
end

# Exact append/read expressions on matches from the original app regexes.
class Tag; end
path=File.join(APP,'app/models/tag.rb')
Tag.class_eval(File.readlines(path)[36..43].join,path,37)
source_record(path,first_line:37,last_line:44)
path=File.join(APP,'app/models/account.rb')
Account.class_eval(File.readlines(path)[73..74].join,path,74)
source_record(path,first_line:74,last_line:75)
hash_text='#ruby'.scan(Tag::HASHTAG_RE).first.first
raise 'actual hashtag regex must match' unless hash_text=='ruby'
exact_expression('M1289',{possible_entries:[],hash_text:hash_text,start_position:0,end_position:5})
path=File.join(APP,'app/lib/extractor.rb')
entries=[]
mentions='@alice @bob'.scan(Account::MENTION_RE).map(&:first)
raise 'actual mention regex must yield two entries' unless mentions==%w[alice bob]
source_segment(path,40,43,locals:{possible_entries:entries,screen_name:mentions.first,start_position:0,end_position:6})
exact_expression('M1299',{possible_entries:entries})

path=File.join(APP,'app/lib/fast_ip_map.rb')
load path
source_record(path)
ip=IPAddr.new('192.0.2.1')
map=FastIpMap.new([ip])
raise 'fixture not found' unless map.include?(ip)
exact_expression('M1332',{},context:map)

# Real kt-paperclip 7.3.0 FileAdapter on an empty local file. Empty content avoids
# MIME detector dependencies; logging/registry are finite library boundaries.
module Paperclip
  class Error < StandardError; end
  class << self
    attr_accessor :io_adapters
    def log(*) = nil
  end
end
%w[io_adapters/abstract_adapter io_adapters/registry tempfile_factory content_type_detector].each do |file|
  path=File.join(ENV.fetch('PAPERCLIP_ROOT'),"lib/paperclip/#{file}.rb")
  load path
  source_record(path)
end
Paperclip.io_adapters=Paperclip::AdapterRegistry.new
path=File.join(ENV.fetch('PAPERCLIP_ROOT'),'lib/paperclip/io_adapters/file_adapter.rb')
load path
source_record(path)
Tempfile.create(['original','.png'],ENV['TMPDIR']) do |file|
  original=Paperclip::FileAdapter.new(file)
  exact_expression('M1683',{intermediate_files:[],original:original,name: :original})
  original.close!
end

# set_common_headers! always installs String keys before a signed redirect.
path=File.join(APP,'app/lib/request.rb')
context=Object.new
headers={}
context.instance_variable_set(:@headers,headers)
source_segment(path,182,182,context:context)
exact_expression('M1904',{},context:context)

# The real controller caster makes a Boolean before passing options to Search.
path=File.join(APP,'app/controllers/application_controller.rb')
context=context_with_params({exclude_unreviewed:'true'})
install_method(context.singleton_class,path,:truthy_param?)
options={exclude_unreviewed:context.truthy_param?(:exclude_unreviewed)}
context.instance_variable_set(:@options,options)
exact_expression('M2013',{},context:context)

context=Object.new
context.instance_variable_set(:@options,{account_id:target.id})
exact_expression('M2148',{syntax_options:[]},context:context)
exact_expression('M2150',{syntax_options:[]},context:context)
exact_expression('M2152',{syntax_options:[],username:target.acct},context:context)

# Collection JSON rendering reaches this actual is_a? argument in CacheConcern.
# Nominal Class[Symbol] is the analyzer spelling of the Symbol class constant;
# the receipt still records ruby_class=Class, not Symbol.
call_argument(File.join(APP,'app/controllers/concerns/cache_concern.rb'),40,:is_a?,['M2643'])

finish('mastodon-witnesses.json')
