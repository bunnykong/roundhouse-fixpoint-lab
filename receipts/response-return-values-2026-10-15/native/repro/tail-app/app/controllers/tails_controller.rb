class TailsController < ApplicationController
  def index
    render plain: "x"
  end

  def show
    head :ok
  end

  def update
    if params[:x]
      redirect_to "/a"
    else
      render plain: "b"
    end
  end

  def destroy
    respond_to do |format|
      format.html { redirect_to "/" }
      format.json { head :no_content }
    end
  end

  private

  def deny
    head :forbidden
  end
end
