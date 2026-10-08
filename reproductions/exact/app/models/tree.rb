class Tree
  def deep(v)
    if v.is_a?(Array)
      v.map { |e| deep(e) }
    elsif v.is_a?(Hash)
      v.transform_values { |e| deep(e) }
    else
      v.to_s
    end
  end
end
