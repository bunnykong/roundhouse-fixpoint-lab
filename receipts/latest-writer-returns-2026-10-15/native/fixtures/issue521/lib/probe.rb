module Probe
  def self.config
    @config ||= Configuration.load!
  end

  class Configuration
    def self.load!
      if config_exists?
        Probe.config.apply_upgrades
      else
        new
      end
    end

    def self.config_exists?
      true
    end

    def apply_upgrades
      self
    end
  end
end

class Client
  def boot
    Probe.config.apply_upgrades
  end
end
