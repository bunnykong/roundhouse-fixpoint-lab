module ApplicationHelper
  def carry(depth, payload)
    if depth > 0
      carry(depth - 1, { payload => payload })
    end
    0
  end
end
