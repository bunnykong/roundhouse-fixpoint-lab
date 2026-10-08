module ApplicationHelper
  def branch_tree(depth)
    if depth <= 0
      [0, nil]
    else
      [0, branch_tree(depth - 1)]
    end
  end
end
