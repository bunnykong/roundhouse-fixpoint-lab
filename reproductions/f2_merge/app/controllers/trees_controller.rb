class TreesController < ApplicationController
  def index
    inner = canonical({ "b" => [1, "x"] })
    @tree = canonical({ "a" => inner.merge("d" => 2), "c" => [inner.merge("e" => nil)] })
  end

  private

  def canonical(value)
    case value
    when Hash then value.sort.to_h { |k, v| [k.to_s, canonical(v)] }
    when Array then value.map { |v| canonical(v) }
    else value
    end
  end
end
