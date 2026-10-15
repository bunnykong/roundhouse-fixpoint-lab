module Prefs
  def self.mode(widget)
    widget.prefs["mode"] || :basic
  end
  def self.c(widget)
    widget.prefs || :en
  end
  def self.d(h)
    h["lang"] || :en
  end
  def self.e(widget)
    widget.prefs["lang"] || "en"
  end
end
