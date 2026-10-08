class ApiClient
  # A class method and an instance method intentionally share a name.
  def self.get(url, options)
    [url, options]
  end

  # Parameter rows are keyed by (class, method) with no receiver side, so the
  # class-side call below lands on this instance method's row: params gains
  # `{ query: params, … }` every round.
  def get(path, params = {})
    options = { query: params, headers: { "Accept" => "application/json" } }
    self.class.get(path, options)
  end
end
