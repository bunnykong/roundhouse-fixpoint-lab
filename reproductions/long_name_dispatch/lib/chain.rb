# Returns that resolve one link per round: first_link -> second_link -> third_link.
class Chain
  def self.first_link(x) = second_link([x])
  def self.second_link(x) = third_link({ "k" => x })
  def self.third_link(x) = x
end
