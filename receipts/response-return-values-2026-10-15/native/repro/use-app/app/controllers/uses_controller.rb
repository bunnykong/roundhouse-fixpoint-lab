class UsesController < ApplicationController
  def create
    sent = deliver
    flash[:notice] = "sent" if sent
  end

  def show
    code = go_back
    logger.info(code.to_s)
  end

  def update
    ok = refuse
    logger.info("refused") if ok
  end

  private

  def deliver
    render plain: "ok"
  end

  def go_back
    redirect_to "/"
  end

  def refuse
    head :forbidden
  end
end
