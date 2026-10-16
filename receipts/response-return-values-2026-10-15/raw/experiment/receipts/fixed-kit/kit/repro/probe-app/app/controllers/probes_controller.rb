class ProbesController < ApplicationController
  def a; v = render(plain: "x"); v.zzz_render; end
  def b; v = redirect_to("/x"); v.zzz_redirect_to; end
  def c; v = redirect_back_or_to("/x"); v.zzz_redirect_back_or_to; end
  def d; v = redirect_back(fallback_location: "/x"); v.zzz_redirect_back; end
  def e; v = head(:ok); v.zzz_head; end
  def f; v = respond_to { |fmt| fmt.html { render plain: "h" } }; v.zzz_respond_to; end
  def g; v = send_data("bytes"); v.zzz_send_data; end
  def h; v = expires_in(60); head :ok; v.zzz_expires_in; end
  def i; v = expires_now; head :ok; v.zzz_expires_now; end
  def j; v = request_http_basic_authentication; v.zzz_basic_auth; end
  def k; v = verify_authenticity_token; head :ok; v.zzz_verify; end
  def l; v = render_to_string(plain: "s"); head :ok; v.zzz_render_to_string; end
  def m; v = send_file("/etc/hosts"); v.zzz_send_file; end
end
