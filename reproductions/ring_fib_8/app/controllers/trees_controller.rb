class TreesController < ApplicationController
  def index
    @tree = m0(6).flatten.size
  end

  private

  def m0(n)
    n.zero? ? [] : [m1(n - 1), m2(n - 1)]
  end

  def m1(n)
    n.zero? ? [] : [m2(n - 1), m3(n - 1)]
  end

  def m2(n)
    n.zero? ? [] : [m3(n - 1), m4(n - 1)]
  end

  def m3(n)
    n.zero? ? [] : [m4(n - 1), m5(n - 1)]
  end

  def m4(n)
    n.zero? ? [] : [m5(n - 1), m6(n - 1)]
  end

  def m5(n)
    n.zero? ? [] : [m6(n - 1), m7(n - 1)]
  end

  def m6(n)
    n.zero? ? [] : [m7(n - 1), m0(n - 1)]
  end

  def m7(n)
    n.zero? ? [] : [m0(n - 1), m1(n - 1)]
  end

end
