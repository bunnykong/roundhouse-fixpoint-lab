class BenchController < ApplicationController
  def index
    @answer = Chain.new.link0
  end
end
