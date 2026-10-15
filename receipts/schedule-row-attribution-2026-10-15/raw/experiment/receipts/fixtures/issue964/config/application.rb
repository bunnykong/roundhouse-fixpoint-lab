module Issue964
  class Application < Rails::Application
    config.autoload_lib(ignore: %w[tasks])
  end
end
