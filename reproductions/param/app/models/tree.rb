class Tree
  def deep(acc, n)
    if n.zero?
      acc
    else
      deep({ inner: acc, size: n }, n - 1)
    end
  end
end
