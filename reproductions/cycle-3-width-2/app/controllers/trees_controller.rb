class TreesController < ApplicationController
  def index
    @tree = walk_0({ "a" => [1, { "b" => "x" }] })
  end

  private

  def walk_0(value)
    if value.is_a?(Hash)
      value.transform_values { |v| walk_1(v) }
    elsif value.is_a?(Array)
      value.map { |v| walk_1(v) }
    else
      value
    end
  end

  def walk_1(value)
    if value.is_a?(Hash)
      value.transform_values { |v| walk_2(v) }
    elsif value.is_a?(Array)
      value.map { |v| walk_2(v) }
    else
      value
    end
  end

  def walk_2(value)
    if value.is_a?(Hash)
      value.transform_values { |v| walk_0(v) }
    elsif value.is_a?(Array)
      value.map { |v| walk_0(v) }
    else
      value
    end
  end
end
