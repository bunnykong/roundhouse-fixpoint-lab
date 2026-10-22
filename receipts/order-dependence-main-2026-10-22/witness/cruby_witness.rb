# CRuby witness: ruby cruby_witness.rb APP_DIR EXPR...
# Loads APP_DIR's app/{models,services,controllers}/*.rb in sorted path order over two empty
# base classes, then evaluates each EXPR and prints its value or the error it raises.
module ActiveRecord; class Base; end; end
module ActionController; class Base; end; end
app = ARGV.shift
%w[models services controllers].each { |d| Dir[File.join(app, "app", d, "*.rb")].sort.each { |f| load f } }
puts "Ruby #{RUBY_VERSION}"
ARGV.each do |expr|
  begin
    puts "#{expr} -> #{eval(expr).inspect}"
  rescue NoMethodError => e
    puts "#{expr} -> #{e.class}: #{e.message}"
  end
end
