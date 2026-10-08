class TreesController < ApplicationController
  def index
    @tree = ApiClient.new.get("items", { "page" => 1 })
  end
end
