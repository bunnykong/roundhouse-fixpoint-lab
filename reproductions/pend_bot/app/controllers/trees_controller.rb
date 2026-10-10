require "json"

class TreesController < ApplicationController
  def index
    @tree = [via_send("label"), via_public_send("shout"), via_method_obj, settings_limit,
             limit_text, from_json("[1, 2]"), ewo_bump([1, 2]), via_lambda, ping(3)]
  end

  # (b) public_send reaches public methods only.
  def shout(s) = s.upcase                                  # "HI"

  private

  # (a) Reached only by a computed send: `render_label`'s parameter is never seeded.
  def via_send(kind) = send("render_#{kind}", 7)
  def render_label(n) = n + 1                              # 8

  # (b) public_send with a computed name.
  def via_public_send(name) = public_send(name, "hi")

  # (c) A Method object.
  def via_method_obj = method(:triple).call(4)
  def triple(n) = n * 3                                    # 12

  # (d) An ivar set reflectively, then a chain on the result: every caller's inputs are known.
  def settings_limit = Settings.new({ "limit" => 5 }).limit  # 5
  def limit_text = settings_limit.to_s.size                # 1

  # (e) A block over a genuinely unknown receiver.
  def from_json(s) = JSON.parse(s).map { |x| bump(x) }
  def bump(x) = x + 1                                      # 2, 3

  # (f) each_with_object binds nothing on Arrays: the argument is pending.
  def ewo_bump(xs) = xs.each_with_object([]) { |x, acc| acc << add_one(x) }
  def add_one(x) = x + 1                                   # 2, 3

  # (g) A lambda kept in a Hash.
  def handlers = { double: ->(x) { twice(x) } }
  def via_lambda = handlers[:double].call(3)
  def twice(x) = x * 2                                     # 6

  # (h) Mutual recursion whose base case is a pending return.
  def ping(n) = n.zero? ? settings_limit : pong(n - 1)    # 5
  def pong(n) = n.zero? ? settings_limit : ping(n - 1)    # 5
end
