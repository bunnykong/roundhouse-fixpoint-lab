class Tree
  def deep(v)
    @trail = [@trail, v.to_s]
    v.is_a?(Array) ? v.map { |e| deep(e) } : @trail
  end
end
