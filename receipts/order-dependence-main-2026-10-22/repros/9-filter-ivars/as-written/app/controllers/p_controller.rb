class PController < ActionController::Base; before_action :one, :two; def show; end; private; def one = @x = 1; def two = @x = "s"; end
