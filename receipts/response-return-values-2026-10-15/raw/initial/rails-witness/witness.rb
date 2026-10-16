# Runtime witness: what Rails' response calls return inside a controller action.
# Real actionpack/actionview (no doubles). One process per Rails version:
#   RAILS_V=8.1.3 GEM_HOME=... GEM_PATH=... ruby witness.rb VIEWDIR > out.json
# Each action stores the value of one call; the request goes through Controller.action(name).call(env).
require "json"
require "logger" # load-order shim: activesupport 6.1 reads Logger::Severity without requiring logger; no effect on response calls
require "tmpdir"
v = ENV.fetch("RAILS_V")
gem "actionpack", v
gem "actionview", v
gem "activesupport", v
require "action_controller"
require "action_view"
require "action_controller/test_case" # ActionController::TestSession only

VIEWS = ARGV.fetch(0)
OBS = {}

def describe(val)
  {
    "class" => val.class.name,
    "is_a_String" => val.is_a?(String),
    "truthy" => val ? true : false,
    "inspect" => val.inspect[0, 120],
  }
end

class ThingsController < ActionController::Base
  self.view_paths = [VIEWS]

  def self.probe(name, &blk)
    define_method(name) do
      val = instance_exec(&blk)
      OBS[name.to_s] = describe(val)
    rescue Exception => e # record, do not hide
      OBS[name.to_s] = { "raised" => e.class.name, "message" => e.message[0, 160] }
      raise
    end
  end

  # render
  probe(:render_plain) { render plain: "hi" }
  probe(:render_plain_status) { render plain: "no", status: :unprocessable_entity }
  probe(:render_html) { render html: "<p>x</p>".html_safe }
  probe(:render_json) { render json: { a: 1 } }
  probe(:render_json_nil) { render json: nil }
  probe(:render_body) { render body: "raw" }
  probe(:render_inline) { render inline: "<%= 1 + 1 %>" }
  probe(:render_action_tpl) { render :show }
  probe(:render_template_status) { render "things/show", status: :not_found }
  probe(:render_template_nolayout) { render :show, layout: false }
  # a helper whose value is render's (the Forem/Mastodon shape), read by the action
  def helper_render
    render plain: "from helper"
  end
  private :helper_render
  probe(:render_via_helper) { helper_render }
  # redirect_to
  probe(:redirect_plain) { redirect_to "/foo" }
  probe(:redirect_see_other) { redirect_to "/foo", status: :see_other }
  probe(:redirect_notice) { redirect_to "/foo", notice: "saved" }
  probe(:redirect_back_fb) { redirect_back(fallback_location: "/home") }
  if ActionController::Base.method_defined?(:redirect_back_or_to) || ActionController::Base.private_method_defined?(:redirect_back_or_to)
    probe(:redirect_back_or_to_fb) { redirect_back_or_to("/home") }
  end
  # head
  probe(:head_ok) { head :ok }
  probe(:head_no_content) { head :no_content }
  probe(:head_not_found_loc) { head :not_found, location: "/x" }
  # respond_to
  probe(:respond_html_render) { respond_to { |f| f.html { render plain: "h" }; f.json { render json: {} } } }
  probe(:respond_json_render) { respond_to { |f| f.html { render plain: "h" }; f.json { render json: { j: 1 } } } }
  probe(:respond_html_redirect) { respond_to { |f| f.html { redirect_to "/r" } } }
  probe(:respond_html_noblock) { respond_to { |f| f.html } }
  probe(:respond_any_head) { respond_to { |f| f.any { head :ok } } }
  # others the registry types Nil
  probe(:send_data_str) { send_data "bytes", filename: "x.txt" }
  probe(:expires_in_val) { r = expires_in(3.minutes, public: true); head :ok; r }
  probe(:expires_now_val) { r = expires_now; head :ok; r }
  probe(:verify_token_get) { r = verify_authenticity_token; head :ok; r }
  probe(:basic_auth_request) { request_http_basic_authentication }
  probe(:render_to_string_val) { r = render_to_string(plain: "s"); head :ok; r }
  probe(:response_body_assign) { self.response_body = "assigned" }
end

ACCEPT = {
  "respond_json_render" => "application/json",
}
REFERER = { "redirect_back_fb" => "http://example.org/came-from", "redirect_back_or_to_fb" => "http://example.org/came-from" }

statuses = {}
ThingsController.public_instance_methods(false).sort.each do |name|
  next if name.to_s.start_with?("_")
  env = Rack::MockRequest.env_for("http://example.org/things/#{name}",
                                  "HTTP_ACCEPT" => ACCEPT.fetch(name.to_s, "text/html"),
                                  "HTTP_REFERER" => REFERER[name.to_s])
  env["rack.session"] = ActionController::TestSession.new
  env["rack.session.options"] = {}
  begin
    status, _headers, _body = ThingsController.action(name).call(env)
    statuses[name.to_s] = status
  rescue Exception => e
    statuses[name.to_s] = "raised #{e.class}"
  end
end

src = {}
%i[render redirect_to head respond_to redirect_back send_data expires_in expires_now verify_authenticity_token request_http_basic_authentication render_to_string].each do |m|
  um = ThingsController.instance_method(m) rescue nil
  src[m.to_s] = um && um.source_location && "#{um.source_location[0].sub(%r{.*/gems/}, "")}:#{um.source_location[1]}"
end
if ThingsController.method_defined?(:redirect_back_or_to) || ThingsController.private_method_defined?(:redirect_back_or_to)
  um = ThingsController.instance_method(:redirect_back_or_to)
  src["redirect_back_or_to"] = "#{um.source_location[0].sub(%r{.*/gems/}, "")}:#{um.source_location[1]}"
end

puts JSON.pretty_generate(
  "rails" => v,
  "ruby" => RUBY_DESCRIPTION,
  "loaded" => Gem.loaded_specs.slice("actionpack", "actionview", "activesupport", "rack").transform_values { |s| s.version.to_s },
  "observations" => OBS.sort.to_h,
  "statuses" => statuses.sort.to_h,
  "sources" => src,
)
