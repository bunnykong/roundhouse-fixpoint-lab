# A plain object whose ivars are set reflectively: no `@limit = ...` anywhere.
class Settings
  def initialize(attrs)
    attrs.each { |k, v| instance_variable_set("@#{k}", v) }
  end

  def limit = @limit
end
