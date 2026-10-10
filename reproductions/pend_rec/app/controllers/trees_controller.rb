class TreesController < ApplicationController
  def index
    @tree = [walk_tree([[1, 2], 3]), even_count(4), odd_count(3)]
  end

  private

  def walker = Walker.new({ "scale" => 2 })
  def walk_tree(t) = walker.walk(t)                                   # [[3, 4], 5]

  # Mutual recursion whose two base cases are pending returns.
  def even_count(n) = n.zero? ? walker.scale : odd_count(n - 1)       # 2
  def odd_count(n) = n.zero? ? walker.scale + 1 : even_count(n - 1)   # 3
end
