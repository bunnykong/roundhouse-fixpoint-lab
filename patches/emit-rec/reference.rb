# Runs a reproduction's TreesController#index under plain CRuby (no Rails) and
# renders its view the way ERB's <%= %> does: html_escape(@tree.to_s).
require "erb"
class ApplicationController; end
app = ARGV.fetch(0)
load File.join(app, "app/controllers/trees_controller.rb")
c = TreesController.new
c.index
tree = c.instance_variable_get(:@tree)
print ERB::Util.html_escape(tree.to_s), "\n"
