class TreesController < ApplicationController
  def index
    @tree = f(3)
  end

  private

  # Same, string-keyed (Hash, not Record), plus an Array position.
  def f(n)
    return { "leaf" => n } if n.zero?
    prev = f(n - 1)
    { "a" => { "b" => prev["a"] }, "c" => [prev["c"]] }
  end
end
