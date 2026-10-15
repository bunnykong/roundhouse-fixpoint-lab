class ProbeController < ApplicationController
 def index
  observe(Source.new.produce)
  observe(Source.new.produce)
 end
 def observe(x)
  x
 end
end
