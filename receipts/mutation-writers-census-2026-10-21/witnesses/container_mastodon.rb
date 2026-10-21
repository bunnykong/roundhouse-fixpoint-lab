# Family: container contents. Row M1545 (Mastodon).
#
# Inside a database transaction, User#send_devise_notification appends to the pending queue
# instead of sending mail. Ruby's queue is [[:confirmation_instructions, ["token"], {}]];
# the candidate types the queue read at user.rb:399 as Array[Bottom], which admits only [].
# Needs the activerecord 8.1.3 and sqlite3 2.10.0 gems.
require_relative 'support'
gem 'activerecord', '8.1.3'
gem 'sqlite3', '2.10.0'
require 'active_record'
require 'active_support/core_ext/object/try'

USER = pinned('mastodon', 'app/models/user.rb',
              'c3d5bf469f7f46d581d59888662ffa801ad03f07b431865eda96d950448bd2b6')

ActiveRecord::Base.establish_connection(adapter: 'sqlite3', database: ':memory:')
ActiveRecord::Schema.verbose = false
ActiveRecord::Schema.define { create_table(:users) { |t| t.string :email } }
class User < ActiveRecord::Base; end
install(User, USER, :send_devise_notification)
install(User, USER, :pending_devise_notifications)
# Boundary: mail delivery. The transaction branch queues and never reaches it.
User.define_method(:render_and_send_devise_message) { |*| abort 'mail boundary reached' }

queue = nil
User.transaction do
  user = User.create!(email: 'queued@example.test')
  user.send(:send_devise_notification, :confirmation_instructions, 'token')
  # Row M1545 is the receiver `pending_devise_notifications` at user.rb:399, bytes 12045...12073.
  queue = user.instance_eval(span(USER, 12045, 12073), USER, 399)
  raise ActiveRecord::Rollback
end
abort 'the notification was not queued' if queue.nil? || queue.empty?

emit('M1545', queue, app: 'mastodon', path: 'app/models/user.rb', line: 399,
     boundary: 'real ActiveRecord transaction on in-memory SQLite; mail delivery not reached')
