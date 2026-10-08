class TreesController < ApplicationController
  def index
    @tree = Tree.new.deep({}, 3)
  end
end
