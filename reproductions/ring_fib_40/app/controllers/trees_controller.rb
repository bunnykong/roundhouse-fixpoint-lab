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
    n.zero? ? [] : [m7(n - 1), m8(n - 1)]
  end

  def m7(n)
    n.zero? ? [] : [m8(n - 1), m9(n - 1)]
  end

  def m8(n)
    n.zero? ? [] : [m9(n - 1), m10(n - 1)]
  end

  def m9(n)
    n.zero? ? [] : [m10(n - 1), m11(n - 1)]
  end

  def m10(n)
    n.zero? ? [] : [m11(n - 1), m12(n - 1)]
  end

  def m11(n)
    n.zero? ? [] : [m12(n - 1), m13(n - 1)]
  end

  def m12(n)
    n.zero? ? [] : [m13(n - 1), m14(n - 1)]
  end

  def m13(n)
    n.zero? ? [] : [m14(n - 1), m15(n - 1)]
  end

  def m14(n)
    n.zero? ? [] : [m15(n - 1), m16(n - 1)]
  end

  def m15(n)
    n.zero? ? [] : [m16(n - 1), m17(n - 1)]
  end

  def m16(n)
    n.zero? ? [] : [m17(n - 1), m18(n - 1)]
  end

  def m17(n)
    n.zero? ? [] : [m18(n - 1), m19(n - 1)]
  end

  def m18(n)
    n.zero? ? [] : [m19(n - 1), m20(n - 1)]
  end

  def m19(n)
    n.zero? ? [] : [m20(n - 1), m21(n - 1)]
  end

  def m20(n)
    n.zero? ? [] : [m21(n - 1), m22(n - 1)]
  end

  def m21(n)
    n.zero? ? [] : [m22(n - 1), m23(n - 1)]
  end

  def m22(n)
    n.zero? ? [] : [m23(n - 1), m24(n - 1)]
  end

  def m23(n)
    n.zero? ? [] : [m24(n - 1), m25(n - 1)]
  end

  def m24(n)
    n.zero? ? [] : [m25(n - 1), m26(n - 1)]
  end

  def m25(n)
    n.zero? ? [] : [m26(n - 1), m27(n - 1)]
  end

  def m26(n)
    n.zero? ? [] : [m27(n - 1), m28(n - 1)]
  end

  def m27(n)
    n.zero? ? [] : [m28(n - 1), m29(n - 1)]
  end

  def m28(n)
    n.zero? ? [] : [m29(n - 1), m30(n - 1)]
  end

  def m29(n)
    n.zero? ? [] : [m30(n - 1), m31(n - 1)]
  end

  def m30(n)
    n.zero? ? [] : [m31(n - 1), m32(n - 1)]
  end

  def m31(n)
    n.zero? ? [] : [m32(n - 1), m33(n - 1)]
  end

  def m32(n)
    n.zero? ? [] : [m33(n - 1), m34(n - 1)]
  end

  def m33(n)
    n.zero? ? [] : [m34(n - 1), m35(n - 1)]
  end

  def m34(n)
    n.zero? ? [] : [m35(n - 1), m36(n - 1)]
  end

  def m35(n)
    n.zero? ? [] : [m36(n - 1), m37(n - 1)]
  end

  def m36(n)
    n.zero? ? [] : [m37(n - 1), m38(n - 1)]
  end

  def m37(n)
    n.zero? ? [] : [m38(n - 1), m39(n - 1)]
  end

  def m38(n)
    n.zero? ? [] : [m39(n - 1), m0(n - 1)]
  end

  def m39(n)
    n.zero? ? [] : [m0(n - 1), m1(n - 1)]
  end

end
