class JProbe
  def self.echo(value)
    value
  end
end
puts JProbe.echo({ "b" => [1, "x", nil] }).inspect
