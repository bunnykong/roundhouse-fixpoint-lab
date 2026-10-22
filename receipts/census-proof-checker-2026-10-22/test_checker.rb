# frozen_string_literal: true
# Tests for checker.rb: each case is a Ruby snippet, the row's expression (by text and occurrence),
# the dump node kind and a claimed type. Negative cases are claims a naive checker would accept.
# Usage: RBENV_VERSION=4.0.7 ruby test_checker.rb
require "minitest/autorun"
require "tmpdir"
require "fileutils"
require_relative "checker"

class ProofCheckerTest < Minitest::Test
  BOT = { "kind" => "bottom" }.freeze
  NIL = { "kind" => "nil" }.freeze
  INT = { "kind" => "int" }.freeze
  STR = { "kind" => "str" }.freeze
  SYM = { "kind" => "sym" }.freeze
  TOP = { "kind" => "untyped" }.freeze

  def arr(e) = { "kind" => "array", "elem" => e }
  def hsh(k, v) = { "kind" => "hash", "key" => k, "value" => v }
  def un(*v) = { "kind" => "union", "variants" => v }
  def cls(id) = { "kind" => "class", "id" => id, "args" => [] }

  def setup
    @dir = Dir.mktmpdir("pc-test")
    FileUtils.mkdir_p(File.join(@dir, "app"))
  end

  def teardown = FileUtils.remove_entry(@dir)

  # Locate the nth occurrence of `target` in `code` and check the claim.
  # `target` is the row's text; `within` (default: target) is a unique larger text that contains it.
  def verdict(code, target, node, type, within: nil, ext: ".rb", extra: {})
    path = File.join(@dir, "app", "t#{ext}")
    File.write(path, code)
    extra.each { |name, text| File.write(File.join(@dir, "app", name), text) }
    within ||= target
    raise "context not unique: #{within}" unless code.b.scan(within.b).size == 1
    a = code.b.index(within.b) + within.b.index(target.b)
    row = { "id" => "T", "app" => "t", "table" => "ir", "key" => "k", "node" => node, "source" => path,
            "span" => { "start" => a, "end" => a + target.bytesize }, "candidate" => type }
    ProofChecker::Checker.new({ "t" => @dir }).check(row)
  end

  def assert_proves(*args, **kw)
    v = verdict(*args, **kw)
    assert_equal "PROVED", v["verdict"], v["reason"]
    v
  end

  def refute_proves(*args, **kw)
    v = verdict(*args, **kw)
    refute_equal "PROVED", v["verdict"], "unexpected proof: #{v['value']}"
    v
  end

  # ---- fresh constructors and literal schemas
  def test_empty_literals
    assert_proves("x = {}\n", "{}", "Hash", hsh(BOT, BOT))
    assert_proves("x = []\n", "[]", "Array", arr(BOT))
    assert_proves("X = %w[].freeze\n", "%w[].freeze", "Send", arr(BOT))
    assert_proves("x = {}\n", "x = {}", "Assign", hsh(STR, TOP))
  end

  def test_literal_schema
    code = "f(status: 200, body: \"\", headers: {})\n"
    assert_proves(code, "status: 200, body: \"\", headers: {}", "Hash", hsh(SYM, un(INT, STR, hsh(BOT, BOT))))
    refute_proves(code, "status: 200, body: \"\", headers: {}", "Hash", hsh(SYM, un(INT, STR)))
    assert_proves("x = {a: 1, \"b\" => nil}\n", "{a: 1, \"b\" => nil}", "Hash", hsh(un(SYM, STR), un(INT, NIL)))
    refute_proves("x = {a: 1, \"b\" => nil}\n", "{a: 1, \"b\" => nil}", "Hash", hsh(SYM, INT))
    assert_proves("x = [1, :a, \"#{'#{y}'}\"]\n", "[1, :a, \"\#{y}\"]", "Array", arr(un(INT, SYM, STR)))
  end

  def test_setter_returns_its_argument_and_safe_navigation_adds_nil
    assert_proves("a.b = []\n", "a.b = []", "Send", arr(BOT))
    refute_proves("a&.b = []\n", "a&.b = []", "Send", arr(BOT))
    assert_proves("a&.b = []\n", "a&.b = []", "Send", un(arr(BOT), NIL))
    assert_proves("a[:k] = {}\n", "a[:k] = {}", "Send", hsh(BOT, BOT))
  end

  def test_sequences_and_branches
    code = "def m\n  @a = {}\n  @b = {}\nend\n"
    assert_proves(code, "@a = {}\n  @b = {}", "Seq", hsh(BOT, BOT))
    code = "def m\n  self.x = {} unless x.is_a?(Hash)\nend\n"
    refute_proves(code, "self.x = {} unless x.is_a?(Hash)", "If", hsh(BOT, BOT))
    assert_proves(code, "self.x = {} unless x.is_a?(Hash)", "If", un(hsh(BOT, BOT), NIL))
    code = "y = case z\n    when 1 then []\n    end\n"
    refute_proves(code, "case z\n    when 1 then []\n    end", "Case", arr(BOT))
  end

  def test_jumps_refuse_body_rows
    code = "def m(c)\n  return [1] if c\n  []\nend\n"
    refute_proves(code, "return [1] if c\n  []", "Seq", arr(BOT))
  end

  # ---- writer enumeration over a local
  def test_writers_fold_into_the_schema
    code = "def m\n  h = {}\n  h[:a] = 1\n  h\nend\n"
    assert_proves(code, "h", "Var", hsh(SYM, INT), within: "  h\nend")
    refute_proves(code, "h", "Var", hsh(BOT, BOT), within: "  h\nend")
  end

  def test_later_writer_does_not_change_an_earlier_read
    code = "def m\n  x = []\n  n = x.size\n  x << 1\n  n\nend\n"
    assert_proves(code, "x", "Var", arr(BOT), within: "x.size")
  end

  def test_loop_carried_writer_counts
    code = "def m\n  x = []\n  3.times { x.first; x << 1 }\nend\n"
    refute_proves(code, "x", "Var", arr(BOT), within: "x.first")
    assert_proves(code, "x", "Var", arr(INT), within: "x.first")
  end

  def test_escapes_and_aliases_make_contents_unknown
    refute_proves("def m\n  x = []\n  foo(x)\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
    refute_proves("def m\n  x = []\n  y = x\n  y << 1\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
    refute_proves("def m\n  x = []\n  x.tap { |a| a << 1 }\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
    refute_proves("def m\n  x = []\n  y = (x << 1)\n  y << :s\n  x\nend\n", "x", "Var", arr(INT), within: "  x\nend")
    refute_proves("def m(o)\n  x = {}\n  x.merge!(o)\n  x\nend\n", "x", "Var", hsh(SYM, INT), within: "  x\nend")
    refute_proves("def m\n  x = []\n  @k = x\n  @k << 1\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
    refute_proves("def m\n  x = []\n  out = items.map { x }\n  out[0] << 1\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
  end

  def test_exclusive_branches
    code = "def m(c, v)\n  x = []\n  if c\n    foo(x)\n  else\n    x\n  end\nend\n"
    assert_proves(code, "x", "Var", arr(BOT), within: "    x\n  end")
    code = "def m(cs, v)\n  x = []\n  cs.each { |c| c ? foo(x) : x }\nend\n"
    refute_proves(code, "x", "Var", arr(BOT), within: ": x }")
  end

  def test_closure_read_after_return_is_not_a_snapshot
    code = "def m\n  x = []\n  cb = -> { x }\n  x << 1\n  cb\nend\n"
    refute_proves(code, "x", "Var", arr(BOT), within: "{ x }")
  end

  def test_nested_containers
    code = "def m\n  x = [[]]\n  x[0] << 1\n  x\nend\n"
    assert_proves(code, "x", "Var", arr(arr(INT)), within: "  x\nend")
    refute_proves(code, "x", "Var", arr(arr(BOT)), within: "  x\nend")
    refute_proves("def m\n  x = [[]]\n  y = x.first\n  y << 1\n  x\nend\n", "x", "Var", arr(arr(BOT)), within: "  x\nend")
    refute_proves("def m\n  h = {a: []}\n  h.each_value { |v| v << 1 }\n  h\nend\n", "h", "Var", hsh(SYM, arr(BOT)), within: "  h\nend")
    assert_proves("def m\n  h = {a: []}\n  h[:a]\nend\n", "h[:a]", "Send", un(arr(BOT), NIL))
    code = "def m(xs)\n  h = {a: []}\n  xs.each { |v| h[:a] << v }\n  h[:a]\nend\n"
    refute_proves(code, "h[:a]", "Send", un(arr(BOT), NIL), within: "  h[:a]\nend")
    assert_proves(code, "h[:a]", "Send", un(arr(TOP), NIL), within: "  h[:a]\nend")
  end

  def test_definite_assignment_and_shadowing
    refute_proves("def m(c)\n  x = [] if c\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
    assert_proves("def m(c)\n  x = [] if c\n  x\nend\n", "x", "Var", un(arr(BOT), NIL), within: "  x\nend")
    assert_proves("def m(i)\n  x = []\n  i.each { |x| x << 1 }\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
    refute_proves("def m\n  x = []\n  binding\n  x\nend\n", "x", "Var", arr(BOT), within: "  x\nend")
  end

  def test_operator_write_and_to_s_keys
    code = "def m(ps)\n  h = {}\n  i = 1\n  ps.each { |p| h[i.to_s] = p; i += 1 }\n  h\nend\n"
    assert_proves(code, "h", "Var", hsh(STR, TOP), within: "  h\nend")
    refute_proves("def m(ps)\n  h = {}\n  ps.each { |k| h[k.to_s] = 1 }\n  h\nend\n", "h", "Var", hsh(STR, INT), within: "  h\nend")
  end

  # ---- dominating guards
  def test_is_a_guard
    code = "def m(x)\n  if x.is_a?(Foo)\n    x\n  end\nend\n"
    assert_proves(code, "x", "Var", cls("Foo"), within: "    x\n")
    refute_proves(code, "x", "Var", cls("Bar"), within: "    x\n")
  end

  def test_guard_invalidated_by_a_write
    code = "def m(x)\n  if x.is_a?(Foo)\n    x = bar\n    x\n  end\nend\n"
    refute_proves(code, "x", "Var", cls("Foo"), within: "    x\n  end")
    code = "def m(x)\n  cb = -> { x = 1 }\n  return unless x.is_a?(Foo)\n  cb.call\n  x\nend\n"
    refute_proves(code, "x", "Var", cls("Foo"), within: "  x\nend")
    code = "def m(x)\n  while c\n    return unless x.is_a?(Foo)\n    y = x\n    x = z\n  end\nend\n"
    refute_proves(code, "x", "Var", cls("Foo"), within: "y = x")
  end

  def test_early_exit_guard
    assert_proves("def m(x)\n  return unless x.is_a?(Foo)\n  x\nend\n", "x", "Var", cls("Foo"), within: "  x\nend")
    assert_proves("def m(x)\n  raise 'no' unless x.kind_of?(Foo)\n  x\nend\n", "x", "Var", cls("Foo"), within: "  x\nend")
    assert_proves("def m(x)\n  return if !x.is_a?(Foo)\n  x\nend\n", "x", "Var", cls("Foo"), within: "  x\nend")
  end

  def test_subclass_instances_are_not_plain_hashes
    refute_proves("def m(v)\n  v if v.is_a?(Hash)\nend\n", "v", "Var", hsh(TOP, TOP), within: "v if")
  end

  def test_case_when_needs_a_known_class
    code = "FOO = /x/\ndef m(x)\n  case x\n  when FOO then x\n  end\nend\n"
    refute_proves(code, "x", "Var", cls("FOO"), within: "then x")
  end

  def test_constant_resolution
    code = "module Outer\n  class Inner\n    def m(x)\n      x if x.is_a?(Status)\n    end\n  end\nend\n"
    extra = { "status.rb" => "module Outer\n  class Status; end\nend\n" }
    refute_proves(code, "x", "Var", cls("Status"), within: "x if", extra: extra)
    assert_proves(code, "x", "Var", cls("Outer::Status"), within: "x if", extra: extra)
  end

  def test_constant_resolution_top_level
    code = "module Outer\n  class Inner\n    def m(x)\n      x if x.is_a?(Status)\n    end\n  end\nend\n"
    assert_proves(code, "x", "Var", cls("Status"), within: "x if")
  end

  def test_constant_defined_in_an_app_superclass_refuses
    extra = { "base.rb" => "class Base\n  class Status; end\nend\n" }
    code = "class Inner < Base\n  def m(x)\n    x if x.is_a?(Status)\n  end\nend\n"
    refute_proves(code, "x", "Var", cls("Status"), within: "x if", extra: extra)
  end

  # ---- exhaustive returns of one def (returns rows)
  def returns_verdict(code, key, type)
    File.write(File.join(@dir, "app", "r.rb"), code)
    row = { "id" => "R", "app" => "t", "table" => "returns", "key" => key, "candidate" => type }
    ProofChecker::Checker.new({ "t" => @dir }).check(row)
  end

  def test_returns
    code = "class A\n  def m(c)\n    return [] if c\n    raise 'x' if c.nil?\n    [1]\n  end\nend\n"
    assert_equal "PROVED", returns_verdict(code, "A#m", arr(INT))["verdict"]
    refute_equal "PROVED", returns_verdict(code, "A#m", arr(BOT))["verdict"]
    code = "class A\n  def m(xs)\n    xs.each { |x| return :found if x }\n    []\n  end\nend\n"
    refute_equal "PROVED", returns_verdict(code, "A#m", arr(BOT))["verdict"]
    assert_equal "PROVED", returns_verdict(code, "A#m", un(arr(BOT), SYM))["verdict"]
    code = "class A\n  def m\n    f = -> { return 1 }\n    {}\n  end\nend\n"
    assert_equal "PROVED", returns_verdict(code, "A#m", hsh(BOT, BOT))["verdict"]
    code = "class A\n  class << self\n    def m = {}\n  end\nend\nclass A\n  def self.m\n    [1]\n  end\nend\n"
    refute_equal "PROVED", returns_verdict(code, "A.m", hsh(BOT, BOT))["verdict"]
    assert_equal "PROVED", returns_verdict(code, "A.m", un(hsh(BOT, BOT), arr(INT)))["verdict"]
    refute_equal "PROVED", returns_verdict(code, "A#m", hsh(BOT, BOT))["verdict"]
  end

  # ---- rows the checker must refuse outright
  def test_refusals
    row = { "id" => "T", "app" => "t", "table" => "params", "key" => "A#m[0]", "candidate" => BOT }
    assert_equal "CANNOT_PROVE", ProofChecker::Checker.new({ "t" => @dir }).check(row)["verdict"]
    refute_proves("def m(**kw)\n  f(**kw)\nend\n", "kw", "KeywordSplat", hsh(BOT, BOT), within: "f(**kw)")
    refute_proves("x = y&.z\n", "y&.z", "BoolOp", TOP)
  end

  def test_template_snippets_are_context_free
    assert_proves("<%= render x, tags: [] %>\n", "tags: []", "Hash", hsh(SYM, arr(BOT)), ext: ".erb")
    refute_proves("<% users = [1] %><%= f(users) %>\n", "users", "Var", arr(BOT), within: "f(users)", ext: ".erb")
  end
end
