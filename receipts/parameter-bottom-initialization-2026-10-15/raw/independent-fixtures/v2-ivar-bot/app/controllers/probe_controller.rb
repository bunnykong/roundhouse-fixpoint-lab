class ProbeController < ApplicationController
 def index
  observe(@never)
 end
 def observe(x)
  x
 end
end
