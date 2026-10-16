require_relative 'witness_support'
gem 'activerecord', '6.1.4.1'
gem 'sqlite3', '1.7.3'
require 'logger'
require 'active_record'
require 'active_support/all'
require 'set'
require 'yaml'
APP = File.join(INPUTS,'forem')

def app_load(relative)
  path = File.join(APP,relative)
  source_record(path,extraction:'entire unchanged file')
  load path
end

def setting_declaration(target,path,key)
  node=nodes_in(path).grep(Prism::CallNode).find do |n|
    n.name==:setting && n.arguments.arguments.first.is_a?(Prism::SymbolNode) && n.arguments.arguments.first.unescaped==key.to_s
  end
  raise "missing setting #{key}" unless node
  target.class_eval(node.location.slice,path,node.location.start_line)
  source_record(path,expression:node.location.slice,line:node.location.start_line)
end

ActiveRecord::Base.establish_connection(adapter:'sqlite3',database:':memory:')
ActiveRecord::Schema.verbose=false
ActiveRecord::Schema.define do
  create_table(:users) { |t| t.string :name; t.string :username; t.integer :comments_count; t.timestamps }
  create_table(:articles) do |t|
    t.integer :user_id; t.string :title; t.string :slug; t.boolean :published
    t.datetime :published_at; t.string :cached_tag_list; t.integer :reading_time; t.timestamps
  end
  create_table(:comments) { |t| t.string :id_code; t.integer :commentable_id; t.string :commentable_type }
  create_table(:settings_communities) { |t| t.string :var; t.text :value }
  create_table(:site_configs) { |t| t.string :var; t.text :value }
  create_table(:listings) { |t| t.string :title }
  create_table(:credits) do |t|
    t.boolean :spent; t.integer :purchase_id; t.string :purchase_type; t.datetime :spent_at
  end
  create_table(:feedback_messages) { |t| t.integer :affected_id; t.integer :offender_id; t.integer :reporter_id }
end
class User < ActiveRecord::Base; end
class Article < ActiveRecord::Base; end
class Comment < ActiveRecord::Base
  belongs_to :commentable, polymorphic:true, optional:true
end
class Listing < ActiveRecord::Base; end
class Credit < ActiveRecord::Base; end
class FeedbackMessage < ActiveRecord::Base; end
# Only the existing scopes needed by the audited queries are installed.
source_segment(File.join(APP,'app/models/credit.rb'),8,8,context:Credit)
source_segment(File.join(APP,'app/models/article.rb'),184,187,context:Article)

# Real Settings::Base setters and AR validations. Only the declarations used
# here are registered; unrelated settings and infrastructure are not booted.
app_load('app/models/concerns/purgeable.rb')
app_load('app/models/application_record.rb')
app_load('app/models/settings/base.rb')
ApplicationConfig = {} # finite environment: no COMMUNITY_NAME override
module Settings
  class Community < Base
    self.table_name=:settings_communities
  end
  class General < Base
    self.table_name='site_configs'
  end
end
setting_declaration(Settings::Community,File.join(APP,'app/models/settings/community.rb'),:community_name)
setting_declaration(Settings::General,File.join(APP,'app/models/settings/general.rb'),:suggested_tags)
setting_declaration(Settings::General,File.join(APP,'app/models/settings/general.rb'),:suggested_users)
app_load('app/validators/existing_published_article_id_validator.rb')
setting_declaration(Settings::General,File.join(APP,'app/models/settings/general.rb'),:feed_pinned_article_id)
app_load('app/models/settings/mandatory.rb')
module Admin
  module Settings
    class BaseController; end
  end
end
app_load('app/controllers/admin/settings/mandatory_settings_controller.rb')
mandatory=Admin::Settings::MandatorySettingsController.new
path=File.join(APP,'app/controllers/admin/settings/mandatory_settings_controller.rb')
trace=TracePoint.new(:line) do |tp|
  next unless tp.path==path && tp.lineno==22
  observe('mandatory-rescue-before-append',tp.binding.local_variable_get(:errors),['F067'],source:path,line:22)
end
result=trace.enable { mandatory.send(:upsert_config,{'community_name'=>'<invalid>'}) }
raise 'real validation did not fail' if result.success?
observe('mandatory-single-rescue-append-result',result.errors,['F008'],source:path,line:22,
        boundary:'real Settings::Base setter/save! and community_name format validator; one error, unchanged return is same array')
app_load('app/services/settings/upsert.rb')
app_load('app/services/settings/general/upsert.rb')
result=Settings::General::Upsert.call({'feed_pinned_article_id'=>'999999'})
raise 'real general validation did not fail' if result.success?
exact_expression('F002',{result:result})

# The full weighted-query constructor uses its real default cases. No SQL is
# executed by this method: AR sanitizes its CASE fragment with finite values.
app_load('app/services/articles/feeds/weighted_query_strategy.rb')
path=File.join(APP,'app/services/articles/feeds/weighted_query_strategy.rb')
hits=0
trace=TracePoint.new(:line) do |tp|
  next unless tp.path==path && tp.lineno==597
  hits+=1
  observe('second-weight-case-receiver',tp.binding.local_variable_get(:values),['F127'],source:path,line:597) if hits==2
end
strategy=trace.enable { Articles::Feeds::WeightedQueryStrategy.new(scoring_configs:{daily_decay_factor:true}) }
raise 'second real case was not reached' unless hits>=2
components=strategy.instance_variable_get(:@relevance_score_components)
raise 'expected one actual configured component' unless components.size==1
observe('sole-configured-append-result',components,['F140'],source:path,line:569,
        boundary:'full unchanged constructor/configure!/build_score_element_from; only one scoring configuration')
exact_expression('F148',context:strategy)

# Full ledger construction queries real finite credit/purchase records.
app_load('app/services/credits/ledger.rb')
listing=Listing.create!(title:'Listing')
Credit.create!(spent:true,purchase_id:listing.id,purchase_type:'Listing',spent_at:Time.utc(2026,1,1))
ledger=Credits::Ledger.new(nil).send(:build_ledger_for,Credit.all)
raise 'one purchase required' unless ledger.size==1 && ledger.first.purchase.id==listing.id
observe('sole-ledger-append-and-block-return',ledger,['F182','F183'],
        source:File.join(APP,'app/services/credits/ledger.rb'),line:60,
        boundary:'full build_ledger_for, actual AR group/select and Item struct; one purchase, no unassociated credits')

# The actual empty-article exporter still returns {"articles.json"=>"[]"}.
# Execute both insertions from the real exporter loop; the second receiver is
# already nonempty. Comments export has the same mandatory String filename.
app_load('app/services/exporter/articles.rb')
app_load('app/services/exporter/comments.rb')
owner=Object.new
owner.define_singleton_method(:articles) { Article.none }
owner.define_singleton_method(:comments) { Comment.none }
exported=Exporter::Articles.new(owner).export
raise 'unexpected exporter result' unless exported=={'articles.json'=>'[]'}
comments_exported=Exporter::Comments.new(owner).export
raise 'unexpected comments exporter result' unless comments_exported=={'comments.json'=>'[]'}
path=File.join(APP,'app/services/exporter/service.rb')
exports={}
name,content=exported.first
source_segment(path,23,23,locals:{exports:exports,name:name,content:content})
exact_expression('F218',{exports:exports})
name,content=comments_exported.first
source_segment(path,23,23,locals:{exports:exports,name:name,content:content})
exact_expression('F219',{exports:exports})

# First affected-user branch returns the freshly nonempty String array.
path=File.join(APP,'app/models/feedback_message.rb')
feedback=FeedbackMessage.new(affected_id:7,offender_id:nil,reporter_id:nil)
exact_expression('F226',{types:[],user_id:7},context:feedback)

# Finite persisted IDs and timestamps are the database boundary. The payload
# data follows the actual Notifications hashes; presentation getters are finite
# boundary values, and are not what these array-mutation rows infer.
user=User.create!(name:'Alice',username:'alice',comments_count:0)
other=User.create!(name:'Bob',username:'bob',comments_count:0)
third=User.create!(name:'Cara',username:'cara',comments_count:0)
article=Article.create!(user_id:user.id,title:'Hello',slug:'hello',published:true,published_at:Time.utc(2026,1,1),cached_tag_list:'ruby',reading_time:1)
user.define_singleton_method(:path) { '/alice' }
user.define_singleton_method(:profile_image_90) { 'https://images.example.test/alice.png' }
article.define_singleton_method(:path) { '/alice/hello' }
article.define_singleton_method(:readable_publish_date) { 'Jan 1' }
article.define_singleton_method(:decorate) { self }
article.define_singleton_method(:cached_tag_list_array) { ['ruby'] }
app_load('app/services/notifications.rb')
json_data={user:Notifications.user_data(user),article:Notifications.article_data(article)}
attrs=[]
exact_expression('F285',{notifications_attributes:attrs,follower:other,notifiable:article,action:'Published',json_data:json_data})
# A second eligible follower reaches this receiver after the first push.
raise 'two distinct eligible follower records needed' unless [other.id,third.id,user.id].uniq.size==3
exact_expression('F287',{notifications_attributes:attrs})

# Seed receiver is fresh before the append; append returns a nonempty ID array.
admin_id=User.first.id
exact_expression('F557',{admins:[],admin_id:admin_id})

# Full original menu DSL proves the inherited String/Symbol mismatch. Feature
# flags affect visibility, not keys; the concrete false flag boundary is enough.
app_load('app/lib/menu.rb')
app_load('app/models/admin_menu.rb')
module FeatureFlag
  def self.enabled?(_flag); false; end
end
menu=AdminMenu.navigation_items
group_name,group=menu.find { |key,value| value[:children].size>1 && value[:children].any? { |item| item[:visible] } }
raise 'actual menu key must be Symbol' unless group_name.is_a?(Symbol)
%w[F589 F590 F592].each { |id| exact_expression(id,{group_name:group_name}) }
path=File.join(APP,'app/helpers/admin_helper.rb')
app_load('app/helpers/admin_helper.rb')
context=Object.new.extend(AdminHelper)
trace=TracePoint.new(:call) do |tp|
  next unless tp.path==path && tp.method_id==:display_name
  observe('actual-display-name-parameter',tp.binding.local_variable_get(:group_name),['F634'],source:path,line:10)
end
trace.enable { context.display_name(group_name) }
finish('forem-witnesses.json')
