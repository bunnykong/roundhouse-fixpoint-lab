class TreesController < ApplicationController
  def index
    @tree = walk({ "k" => [1, 2] })
  end

  private

  # Block parameters come from the receiver union's FIRST concrete arm
  # (send.rs block_params_for). A Hash-only row binds |key, val| = (String,
  # Array[Integer]) and passes an Array back in; a row with an Array arm binds
  # val to nothing, the Array observation disappears, and the row flips back.
  def walk(v)
    v.each { |key, val| walk(val) unless val.nil? }
    v
  end
end
