class PController < ActionController::Base; before_action :two, :one; def show; end; private; def one = @x = 1; def two = @x = "s"; end
