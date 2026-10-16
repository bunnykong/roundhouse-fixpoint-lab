class WidgetsController < ApplicationController
  def show
    widget = Widget.find(params[:id])
    render json: { mode: Prefs.mode(widget), c: Prefs.c(widget), d: Prefs.d(JSON.parse(widget.name)), e: Prefs.e(widget) }
  end
end
