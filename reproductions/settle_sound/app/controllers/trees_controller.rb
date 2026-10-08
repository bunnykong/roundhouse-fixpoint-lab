class TreesController < ApplicationController
  def index
    @tree = canonical({ "a" => canonical({ "b" => 1 }).merge("d" => 2) })
  end

  private

  def canonical(value)
    case value
    when Hash then value.sort.to_h { |k, v| [k.to_s, canonical(v)] }
    else value
    end
  end
end
