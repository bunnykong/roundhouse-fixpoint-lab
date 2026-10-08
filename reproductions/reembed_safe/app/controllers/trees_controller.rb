class TreesController < ApplicationController
  def index
    @tree = f(3)
  end

  private

  # the re-embedding example in its safe-navigation form (the
  # original raises NoMethodError for n >= 1): R = nil | {a: B}, B = {b: T}, T = nil | {b: T}.
  def f(n)
    n.zero? ? nil : { a: { b: f(n - 1)&.[](:a) } }
  end
end
