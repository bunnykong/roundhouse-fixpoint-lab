class TreesController < ApplicationController
  def index
    @tree = Tree.new.deep({ a: [1, { b: "c" }] })
  end
end
