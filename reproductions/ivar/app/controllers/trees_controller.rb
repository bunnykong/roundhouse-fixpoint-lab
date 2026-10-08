class TreesController < ApplicationController
  def index
    @tree = Tree.new.deep([1, [2, "x"]])
  end
end
