class TreesController < ApplicationController
  def index
    @list = []
    @list = [@list, "x"] if params[:wrap]
    @tree = @list
  end
end
