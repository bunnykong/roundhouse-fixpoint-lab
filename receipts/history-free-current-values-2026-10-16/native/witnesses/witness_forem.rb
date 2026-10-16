require_relative 'witness_support'
gem 'activerecord', '6.1.4.1'
gem 'sqlite3', '1.7.3'
require 'logger'
require 'active_record'
require 'active_support/core_ext/string/filters'
require 'active_support/core_ext/object/blank'
require 'twitter'
APP = File.join(INPUTS, 'forem')

ActiveRecord::Base.establish_connection(adapter: 'sqlite3', database: ':memory:')
ActiveRecord::Schema.verbose = false
ActiveRecord::Schema.define do
  create_table(:tweets) do |t|
    t.string :twitter_name
    t.string :twitter_uid
    t.integer :twitter_user_followers_count
    t.integer :twitter_user_following_count
    t.string :twitter_username
    t.boolean :user_is_verified
  end
  create_table(:users) { |t| t.datetime :created_at }
  create_table(:articles) { |t| t.datetime :published_at }
end
class Tweet < ActiveRecord::Base
  attr_accessor :remote_profile_image_url
end
class User < ActiveRecord::Base; end
class Article < ActiveRecord::Base; end
path = File.join(APP, 'app/models/tweet.rb')
install_method(Tweet.singleton_class, path, :extract_user_attributes)
tweet = Tweet.new
status = Twitter::Tweet.new(id: 101, user: { id: 7, name: '', screen_name: '', followers_count: nil, friends_count: nil })
raise unless Tweet.extract_user_attributes(tweet, status).equal?(tweet)
%w[F052 F055 F057 F059].each { |id| exact_expression(id, { tweet: tweet, status: status }) }
exact_expression('F040', { tweet: tweet })
raise 'save! witness did not persist' unless tweet.persisted?
call_argument(File.join(APP, 'app/models/comment.rb'), 95, :includes, ['F075'])

%w[user article].each do |name|
  path = File.join(APP, "app/services/search/#{name}.rb")
  source_record(path, extraction: 'entire unchanged file')
  load path
end
[[nil, :desc], [:created_at, :asc], ['created_at', :desc], [:other, nil]].each do |by, direction|
  observe('Search::User.sort', Search::User.send(:sort, User.all, by, direction), ['F027'], input: [by, direction])
end
[['query', nil, nil], [nil, :published_at, :asc], [nil, nil, nil]].each do |term, by, direction|
  observe('Search::Article.sort gain', Search::Article.send(:sort, Article.all, term, by, direction), [], input: [term, by, direction])
end
finish('forem-witnesses.json')
