class TreesController < ApplicationController
  def index
    @state = step(@state || { "n" => 0 })
    @tree = @state
  end

  def show
    @state = step({ "m" => [@state, { "k" => 1 }] })
  end

  private

  # Not recursive. The ivar threads the result back into the parameter.
  def step(s)
    { "prev" => s, "all" => [s, { "z" => 2 }] }
  end
end
