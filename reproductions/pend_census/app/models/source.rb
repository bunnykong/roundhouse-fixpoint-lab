# One method per pending source; each returns a core value at runtime. The *_len methods chain
# `.to_s.size` on the source, where the shared-type baseline conversion fallback keeps an Integer.
class Source
  def initialize(opts) = opts.each { |k, v| instance_variable_set("@#{k}", v) }

  def ivar_reflective = @limit                                              # 5
  def ivar_get = instance_variable_get(:@limit)                             # 5
  def named_capture(s) = (/(?<num>\d+)/ =~ s; num)                          # "12"
  def for_var(xs) = (for x in xs do end; x)                                 # 2
  def slice_param(xs) = xs.each_slice(2).map { |a, b| ident(a) }.first      # 1
  def zip_param(xs) = xs.zip(xs).map { |a, b| ident2(b) }.first             # 1
  def inject_acc(xs) = xs.inject(0) { |acc, x| ident3(acc) + x }            # 3
  def ewo_param(xs) = xs.each_with_object([]) { |x, acc| acc << ident4(x) }.first   # 1
  def loop_break = loop { break 5 }                                         # 5
  def catch_value = catch(:done) { throw :done, 6 }                         # 6
  def enum_value = Enumerator.new { |y| y << 7 }.first                      # 7
  def via_missing = undefined_thing(8)                                      # 8
  def method_missing(name, *args) = args.first
  def respond_to_missing?(*) = true
  def defined_dyn = dyn_value                                               # 9
  define_method(:dyn_value) { 9 }
  def aliased = lim_alias                                                   # 5
  alias_method :lim_alias, :ivar_reflective

  def ident(v) = v
  def ident2(v) = v
  def ident3(v) = v
  def ident4(v) = v

  def ivar_reflective_len = ivar_reflective.to_s.size                       # 1
  def named_capture_len(s) = named_capture(s).to_s.size                     # 2
  def loop_break_len = loop_break.to_s.size                                 # 1
  def via_missing_len = via_missing.to_s.size                               # 1
end

class Base
  def doubled(x) = x * 2                                                    # 10 (reached through zsuper only)
end

class Kid < Base
  def doubled(x) = super
end
