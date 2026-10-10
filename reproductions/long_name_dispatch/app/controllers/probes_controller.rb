class ProbesController < ApplicationController
  def index
    @value = Probe.new.reader
  end
end
