class TreesController < ApplicationController
  def index
    sc = Scanner.new
    @tree = [sc.capture("x12"), sc.last_for([1, 2]), sc.capture_len("x12")]
  end
end
