class TreesController < ApplicationController
  def index
    @tree = f(3)
  end

  private

  # the level-1 counterexample: a projection of the recursive result is
  # re-embedded one level deeper than it came from.
  def f(n)
    n.zero? ? nil : { a: { b: f(n - 1)[:a] } }
  end
end
