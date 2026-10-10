# Options arrive reflectively, so `@scale` has no assignment the analyzer sees.
class Walker
  def initialize(opts)
    opts.each { |k, v| instance_variable_set("@#{k}", v) }
  end

  def scale = @scale

  # A recursive type whose leaves hang off the pending return: scale + node.
  def walk(node) = node.is_a?(Array) ? node.map { |n| walk(n) } : scale + node
end
