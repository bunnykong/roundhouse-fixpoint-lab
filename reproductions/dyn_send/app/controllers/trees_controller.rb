class TreesController < ApplicationController
  FIELDS = %i[title tags].freeze

  def index
    @tree = payload
  end

  def title = "t"

  def tags = ["a", { "k" => 1 }]

  # Serializer shape: a dynamic public_send. The analyzer answers it with the
  # union of every instance method's return, payload's own included.
  def payload
    FIELDS.to_h { |f| [f.to_s, public_send(f)] }.merge("meta" => { "v" => 1 })
  end
end
