# Locals the typer cannot bind, inside a plain class (a library method).
class Scanner
  def capture(s)
    /(?<num>\d+)/ =~ s
    num                                  # "12"
  end

  def last_for(xs)
    for x in xs do end
    x                                    # 2
  end

  def capture_len(s) = capture(s).size   # 2
end
