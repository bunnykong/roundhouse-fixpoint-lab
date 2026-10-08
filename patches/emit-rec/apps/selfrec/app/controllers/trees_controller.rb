class TreesController < ApplicationController
  def index
    @tree = walk({ "a" => [1, { "b" => "x" }] })
  end

  private

  def walk(value)
    if value.is_a?(Hash)
      value.transform_values { |v| walk(v) }
    elsif value.is_a?(Array)
      value.map { |v| walk(v) }
    else
      value
    end
  end
end
