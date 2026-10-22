# Rails witness: ruby rails_witness.rb APP_DIR CONTROLLER...
# Loads APP_DIR/app/controllers/*.rb (sorted) into real ActionPack, renders each controller's
# `show` from APP_DIR/app/views, and prints the body or the error the probe's `.zzz` raises
# (Ruby names the receiver's class, which is the runtime type the analyzer should give).
gem "actionpack", "8.1.4"
gem "actionview", "8.1.4"
require "action_controller"
require "rack/mock"

app = ARGV.shift
Dir[File.join(app, "app/controllers/*.rb")].sort.each { |f| load f }
ActionController::Base.prepend_view_path(File.join(app, "app/views"))
puts "Ruby #{RUBY_VERSION}, ActionPack #{ActionPack::VERSION::STRING}"
ARGV.each do |name|
  klass = Object.const_get(name)
  env = Rack::MockRequest.env_for("/#{klass.controller_path}")
  begin
    status, _h, body = klass.action(:show).call(env)
    text = +""
    body.each { |s| text << s }
    puts "#{name}#show -> #{status} #{text.strip.inspect}"
  rescue Exception => e
    where = e.class.name.include?("Template::Error") ? "view" : "action"
    e = e.cause if where == "view"
    puts "#{name}#show -> (#{where}) #{e.class}: #{e.message.lines.first.strip}"
  end
end
