class TreesController < ApplicationController
  def index
    @tree = pick([1, 2], 2).bit_length   # at run time pick returns 3, an Integer
  end

  private

  # The analyzer cannot type `inject`, so this return is genuinely gradual
  # (Untyped) on one path and a String on another.
  def pick(xs, n)
    return xs.inject(:+) if n.zero?
    n > 5 ? "big" : pick(xs, n - 1)
  end
end
