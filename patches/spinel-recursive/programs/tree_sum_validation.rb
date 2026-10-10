# Sum Integer leaves in a recursive Hash/Array tree; String and nil leaves contribute zero.
def sum_leaves(value)
  case value
  when Hash
    total = 0
    value.each_value { |v| total += sum_leaves(v) }
    total
  when Array
    total = 0
    value.each { |v| total += sum_leaves(v) }
    total
  when Integer
    value
  else
    0
  end
end

input = { "a" => [1, { "b" => [2, 3, [4, nil]] }], "c" => [5, { "d" => [6, 7, "x"] }] }
n = ARGV.empty? ? 1 : ARGV[0].to_i
result = 0
n.times { result = sum_leaves(input) }
puts result

puts sum_leaves(nil).inspect
puts sum_leaves(0).inspect
puts sum_leaves(-1).inspect
puts sum_leaves("").inspect
puts sum_leaves([]).inspect
puts sum_leaves({  }).inspect
puts sum_leaves([1, 2]).inspect
puts sum_leaves({ "z" => [], "a" => nil }).inspect
puts sum_leaves([[{ "a" => [2] }]]).inspect
puts sum_leaves("").inspect
puts sum_leaves(nil).inspect
puts sum_leaves([]).inspect
puts sum_leaves({  }).inspect
puts sum_leaves({ "k0" => [] }).inspect
puts sum_leaves({  }).inspect
puts sum_leaves([{ "k3" => { "k3" => "x", "k2" => ["two words", "", { "k2" => -8, "k0" => 10, "k1" => "two words" }, { "k2" => "two words", "k0" => "two words", "k1" => nil }], "k0" => { "k1" => ["x"], "k0" => [] }, "k1" => nil }, "k1" => "", "k2" => {  }, "k0" => ["", [nil], [15]] }, {  }, [[16, { "k0" => "x", "k1" => ["x", -21, "two words"] }, [], 0], [{ "k1" => nil, "k2" => "two words", "k0" => [nil] }]], [{  }, [], { "k1" => {  }, "k0" => 19 }, { "k0" => "two words" }]]).inspect
puts sum_leaves({ "k0" => nil }).inspect
puts sum_leaves({ "k2" => { "k1" => [{ "k0" => ["x", 1, "two words"], "k1" => "", "k3" => nil, "k2" => "x" }, [], { "k0" => [29, "x"], "k1" => { "k2" => "two words", "k3" => 21, "k1" => "two words", "k0" => "two words" } }, "x"], "k0" => "x" }, "k1" => { "k0" => ["x", "two words", { "k1" => { "k3" => nil, "k1" => "x", "k0" => -28, "k2" => "x" }, "k0" => "x" }], "k1" => [14, [nil, {  }, { "k1" => "two words", "k0" => nil }, { "k1" => "two words", "k0" => "" }], { "k1" => "two words", "k0" => { "k0" => 10, "k1" => "", "k2" => nil, "k3" => -1 } }, [{ "k1" => "", "k0" => "two words", "k2" => -22 }, { "k1" => "two words", "k0" => nil }, ["two words", ""]]] }, "k3" => 6, "k0" => -18 }).inspect
puts sum_leaves({ "k0" => { "k2" => "x", "k0" => "x", "k1" => "x", "k3" => ["x", "x"] } }).inspect
puts sum_leaves({ "k0" => [[]] }).inspect
puts sum_leaves(-2).inspect
puts sum_leaves(22).inspect
puts sum_leaves(13).inspect
puts sum_leaves([[[], 11, [{ "k0" => { "k0" => nil, "k2" => nil, "k1" => -22 }, "k1" => 12 }], "x"]]).inspect
puts sum_leaves(23).inspect
puts sum_leaves("").inspect
puts sum_leaves("two words").inspect
puts sum_leaves([{ "k1" => "", "k2" => 7, "k0" => [["x", "x"], { "k0" => { "k0" => "", "k2" => "", "k1" => "x" }, "k1" => [22, "two words", "x"], "k2" => { "k0" => "x", "k1" => nil }, "k3" => "" }, {  }] }, "x", nil]).inspect
puts sum_leaves({ "k0" => [[], [-24, [{ "k0" => 27 }, [nil, nil, "two words"], ""], { "k2" => [nil], "k1" => [], "k0" => [-2], "k3" => "x" }, {  }]], "k1" => { "k0" => -22, "k2" => { "k0" => { "k0" => ["", "", "", "two words"] }, "k1" => ["", ["", "two words", 25, "two words"]], "k3" => [{ "k0" => "" }], "k2" => [[], { "k0" => nil }, 5, { "k0" => -14, "k2" => "", "k1" => "x" }] }, "k3" => nil, "k1" => 20 } }).inspect
puts sum_leaves("").inspect
puts sum_leaves(nil).inspect
puts sum_leaves([[[[{ "k2" => "", "k0" => -29, "k1" => "two words" }]], { "k1" => [["x", "", "", ""]], "k0" => { "k2" => { "k0" => "", "k1" => -5 }, "k1" => 0, "k0" => [-4, ""] } }, [[["two words", nil], "", { "k0" => nil, "k1" => "" }, { "k1" => -23, "k0" => nil, "k2" => nil }], {  }, [[nil], { "k1" => -9, "k2" => "two words", "k0" => -24 }], [3, "two words", "x"]]], { "k0" => -23, "k1" => ["", [{ "k1" => "x", "k2" => "", "k0" => nil }, 24, {  }], "x", { "k2" => "x", "k0" => ["x"], "k1" => "" }], "k2" => [] }, "two words", { "k0" => [nil] }]).inspect
puts sum_leaves("").inspect
puts sum_leaves(nil).inspect
puts sum_leaves(["two words", nil, [nil, { "k2" => "", "k0" => ["two words", { "k2" => "x", "k0" => "", "k1" => nil, "k3" => nil }, { "k1" => "", "k2" => nil, "k0" => 5 }], "k1" => "two words" }], "two words"]).inspect
puts sum_leaves({ "k0" => { "k0" => nil }, "k2" => -14, "k1" => [{ "k0" => [[""], { "k2" => "x", "k3" => -10, "k1" => nil, "k0" => "" }, {  }, "x"], "k2" => nil, "k1" => [{ "k3" => "two words", "k2" => "x", "k0" => "two words", "k1" => nil }, nil, [nil, "x", nil], ["two words", ""]] }, []] }).inspect
puts sum_leaves({ "k0" => { "k3" => ["", [], { "k0" => [] }, [[6, "x", -4, nil], "two words"]], "k2" => { "k0" => [[nil, "two words"], { "k3" => nil, "k1" => "two words", "k0" => -30, "k2" => "" }], "k3" => [16], "k1" => { "k0" => [], "k1" => 12 }, "k2" => "" }, "k1" => "", "k0" => { "k0" => "" } }, "k1" => { "k0" => { "k3" => "x", "k0" => [[], "two words", "two words", ""], "k1" => {  }, "k2" => ["", ["x", "two words", 25], ["two words", 28, "x"], 22] }, "k3" => 8, "k1" => [8, ["two words"]], "k2" => {  } }, "k2" => [{  }, [], []] }).inspect
puts sum_leaves(nil).inspect
puts sum_leaves("two words").inspect
puts sum_leaves([]).inspect
puts sum_leaves({ "k1" => "x", "k0" => { "k0" => { "k0" => { "k0" => { "k0" => "", "k1" => "x", "k3" => "x", "k2" => "two words" } }, "k1" => { "k0" => [30, "two words"], "k1" => {  } } }, "k3" => 17, "k1" => { "k3" => [{ "k1" => "two words", "k2" => "two words", "k0" => "" }, ["two words", "two words", "two words", nil], { "k1" => "", "k0" => 20, "k2" => "two words", "k3" => -4 }, ""], "k1" => "", "k0" => "x", "k2" => "" }, "k2" => [{ "k3" => -28, "k0" => [""], "k2" => { "k2" => "x", "k0" => -7, "k1" => -5 }, "k1" => { "k2" => 4, "k0" => nil, "k1" => -27 } }] }, "k3" => { "k0" => "" }, "k2" => [{ "k2" => [{ "k0" => "", "k1" => "x", "k2" => nil, "k3" => "" }, 24], "k1" => { "k1" => {  }, "k3" => [nil, ""], "k0" => { "k0" => "" }, "k2" => nil }, "k0" => {  } }, { "k1" => { "k2" => { "k3" => "", "k0" => "two words", "k2" => "x", "k1" => nil }, "k0" => { "k2" => "x", "k0" => "two words", "k1" => "x" }, "k1" => {  } }, "k2" => "two words", "k0" => "", "k3" => [["two words", ""], ["two words", ""], { "k3" => 18, "k2" => nil, "k1" => "x", "k0" => "x" }] }, [{ "k1" => nil, "k0" => 18 }, "two words"]] }).inspect
puts sum_leaves({ "k0" => [], "k2" => { "k1" => "x", "k0" => [[{  }, "x"], { "k1" => "x", "k0" => ["two words", nil, "two words", ""] }] }, "k1" => "" }).inspect
puts sum_leaves("").inspect
puts sum_leaves([[], [["two words"], { "k0" => -22, "k1" => { "k3" => [7, 17, "two words"], "k2" => "two words", "k0" => {  }, "k1" => [] }, "k2" => "two words" }, "", {  }], [], []]).inspect
puts sum_leaves({ "k0" => ["", { "k2" => { "k1" => "two words", "k0" => "", "k3" => [nil], "k2" => "x" }, "k0" => [{ "k0" => "two words", "k1" => "two words" }], "k3" => { "k0" => { "k1" => nil, "k2" => "two words", "k3" => "x", "k0" => "x" }, "k3" => [nil, -7], "k2" => "", "k1" => { "k0" => "two words", "k2" => "", "k3" => "x", "k1" => -24 } }, "k1" => [[-21, -7, "two words"]] }], "k1" => "" }).inspect
puts sum_leaves([nil]).inspect
puts sum_leaves([]).inspect
puts sum_leaves("two words").inspect
puts sum_leaves("").inspect
puts sum_leaves({ "k2" => [{ "k1" => "x", "k2" => ["", 0, [1]], "k0" => [{ "k2" => "", "k0" => "x", "k1" => nil }, 23, [nil]] }, [-22, nil, []]], "k0" => { "k0" => "two words" }, "k1" => [-16, [[["x"]], 22, { "k0" => { "k0" => 29 }, "k2" => -15, "k1" => {  } }, [[nil, "x"]]], "two words"] }).inspect
puts sum_leaves(nil).inspect
puts sum_leaves([[{ "k0" => [] }, { "k0" => "two words" }], ""]).inspect
puts sum_leaves([{  }, {  }, nil, -8]).inspect
puts sum_leaves([{ "k1" => { "k2" => { "k2" => { "k0" => "x" }, "k1" => [""], "k0" => ["", "x", 12, 17], "k3" => ["two words", "two words", 4] }, "k3" => nil, "k0" => -12, "k1" => "two words" }, "k2" => {  }, "k0" => [{ "k0" => 15 }] }]).inspect
puts sum_leaves("").inspect
puts sum_leaves("").inspect
puts sum_leaves({  }).inspect
puts sum_leaves("two words").inspect
puts sum_leaves([["x", { "k0" => "", "k1" => { "k1" => nil, "k0" => -17, "k2" => [] } }, { "k1" => [[]], "k0" => {  } }], nil]).inspect
puts sum_leaves(["x", "x"]).inspect
puts sum_leaves({ "k0" => "x" }).inspect
puts sum_leaves("").inspect
puts sum_leaves([{  }, "x", {  }, { "k0" => "", "k1" => [[{ "k0" => nil, "k2" => "", "k1" => "x" }, 5, {  }], { "k1" => "x", "k0" => [-20, "", 18], "k2" => [nil, ""] }] }]).inspect
puts sum_leaves([["x", { "k0" => "x" }, [{  }], { "k2" => nil, "k3" => [{ "k0" => -9, "k1" => -13, "k2" => "" }, [], { "k0" => "x", "k3" => "two words", "k2" => "", "k1" => "two words" }], "k0" => {  }, "k1" => { "k1" => ["", "", "x", "two words"], "k3" => 23, "k0" => nil, "k2" => { "k1" => "", "k0" => "", "k2" => "" } } }], { "k1" => {  }, "k0" => { "k0" => { "k0" => [], "k1" => { "k0" => "", "k1" => -17 } } } }, { "k1" => { "k1" => [{  }, [], { "k0" => "" }, { "k2" => "x", "k0" => "x", "k1" => 16 }], "k0" => ["two words", { "k0" => "" }] }, "k0" => [[], [-14], {  }, ""], "k2" => { "k0" => [["x", nil, ""], [nil, "", nil], [nil, nil]], "k1" => { "k0" => "" }, "k2" => "x", "k3" => { "k3" => "x", "k0" => "x", "k2" => [], "k1" => "" } }, "k3" => "" }, nil]).inspect
puts sum_leaves(nil).inspect
puts sum_leaves("two words").inspect
puts sum_leaves({ "k0" => { "k0" => [{ "k3" => "two words", "k2" => "two words", "k1" => ["x", 10, "two words", 24], "k0" => ["two words", ""] }, [{ "k1" => "", "k0" => "x" }, -14, { "k0" => "two words" }, {  }]] } }).inspect
puts sum_leaves({  }).inspect
puts sum_leaves([{ "k2" => [{  }, { "k1" => { "k0" => "" }, "k0" => ["x", 2, nil], "k3" => [-13, 9, 25], "k2" => ["two words", nil, 3, ""] }], "k3" => [], "k1" => 5, "k0" => { "k1" => -14, "k0" => 8, "k2" => "", "k3" => [{ "k0" => "x" }, [""], nil] } }]).inspect
puts sum_leaves([{ "k3" => [[nil, {  }, {  }, ["", "two words", ""]], "two words", "", { "k0" => [nil], "k2" => "two words", "k3" => [], "k1" => [-13, "", ""] }], "k0" => "", "k1" => [["two words", "two words", nil]], "k2" => [] }, ["", -6, [{ "k1" => ["", 28], "k2" => "two words", "k0" => [] }, ["x", { "k0" => "two words", "k1" => -6 }, { "k1" => nil, "k0" => 27 }, ""], { "k0" => nil, "k2" => { "k1" => "x", "k0" => -26 }, "k1" => {  } }]]]).inspect
puts sum_leaves({ "k1" => [[[], "", [{ "k0" => nil }]], [[["x", "", nil, nil]]], ""], "k0" => [] }).inspect
puts sum_leaves({ "k1" => [{ "k1" => nil, "k0" => {  }, "k2" => "", "k3" => "two words" }, [], [[[nil, nil, nil, nil], "two words", [15, ""], { "k1" => "x", "k2" => 16, "k0" => nil, "k3" => "two words" }]], {  }], "k0" => [12, "x"], "k2" => 7, "k3" => [] }).inspect
puts sum_leaves("").inspect
puts sum_leaves({ "k0" => { "k0" => ["two words"] }, "k1" => { "k1" => -17, "k2" => "x", "k0" => nil } }).inspect
puts sum_leaves([[[{ "k2" => [-17, "two words", 2, "two words"], "k1" => ["two words"], "k3" => [], "k0" => "two words" }], [{ "k1" => { "k0" => "two words", "k1" => "" }, "k2" => { "k2" => "x", "k0" => "two words", "k1" => 4, "k3" => nil }, "k0" => {  } }]], { "k1" => { "k0" => "x" }, "k3" => { "k1" => { "k0" => ["x", -3, nil], "k1" => "x", "k3" => "two words", "k2" => { "k0" => "x" } }, "k2" => { "k0" => nil, "k2" => [26, "two words", "", -1], "k3" => "x", "k1" => "x" }, "k3" => [], "k0" => "two words" }, "k2" => [[-10, [nil], ["two words", nil, -29, ""]]], "k0" => "two words" }, nil, "two words"]).inspect
puts sum_leaves([]).inspect
puts sum_leaves("").inspect
puts sum_leaves({ "k0" => [], "k1" => [[{  }, -6, [25, "x", ["two words"], ["two words", "x", "x", 16]], { "k0" => "x" }], "", ["x", [{ "k0" => "" }], ["", ["", "x", "two words", -5]], { "k1" => { "k2" => "x", "k1" => "two words", "k3" => nil, "k0" => 11 }, "k3" => nil, "k0" => [nil, "", nil, 0], "k2" => [nil, ""] }]] }).inspect
puts sum_leaves("").inspect
puts sum_leaves([{ "k0" => ["two words", nil, [[], "x"]] }, 14, [["two words", [[-21, nil], { "k0" => "" }], [{ "k1" => "x", "k2" => nil, "k0" => "x" }, { "k3" => "", "k2" => -28, "k0" => -3, "k1" => "two words" }, ["two words"], []]]]]).inspect
puts sum_leaves({ "k0" => [""], "k1" => "two words", "k2" => { "k0" => "two words", "k1" => [], "k2" => "x", "k3" => { "k0" => { "k0" => [] }, "k1" => "two words" } }, "k3" => [] }).inspect
puts sum_leaves({ "k0" => "x" }).inspect
puts sum_leaves([nil]).inspect
puts sum_leaves({  }).inspect
puts sum_leaves("x").inspect
puts sum_leaves({ "k1" => {  }, "k0" => { "k1" => { "k0" => { "k3" => {  }, "k0" => {  }, "k2" => "x", "k1" => ["two words", "x"] }, "k1" => [] }, "k0" => { "k0" => { "k0" => { "k1" => -28, "k0" => 11, "k2" => -29 } }, "k2" => [{ "k0" => nil }, -1, -20], "k1" => nil, "k3" => "x" } } }).inspect
puts sum_leaves([3]).inspect
puts sum_leaves({ "k0" => "", "k2" => [-30, ["two words"]], "k1" => { "k0" => { "k2" => -18, "k0" => "two words", "k1" => [{ "k0" => nil }] }, "k1" => [] }, "k3" => [nil] }).inspect
puts sum_leaves("x").inspect
puts sum_leaves({ "k1" => [[], { "k1" => [], "k0" => { "k2" => -21, "k0" => { "k1" => "x", "k0" => nil }, "k1" => "", "k3" => [nil, "x", "x"] }, "k2" => { "k0" => { "k0" => -11 } }, "k3" => {  } }, "two words", [{ "k0" => { "k1" => nil, "k3" => "", "k2" => -1, "k0" => nil }, "k3" => {  }, "k2" => [nil], "k1" => [] }, [{  }, "x", { "k2" => "x", "k1" => "", "k0" => "two words" }, { "k1" => "two words", "k0" => "", "k2" => "x" }]]], "k0" => "" }).inspect
puts sum_leaves({ "k0" => { "k0" => "x" }, "k1" => "x", "k2" => [{ "k0" => nil, "k1" => { "k0" => "two words", "k1" => "" } }] }).inspect
puts sum_leaves({ "k1" => { "k2" => [{  }, [-1, [13, 20]]], "k1" => "", "k0" => ["two words"] }, "k0" => 12, "k2" => { "k0" => { "k2" => [[]], "k0" => [{ "k0" => nil, "k1" => nil, "k2" => "x" }, -26], "k1" => {  }, "k3" => { "k1" => ["", "", "", ""], "k2" => "two words", "k0" => "" } }, "k1" => "x", "k2" => "", "k3" => { "k3" => [-7], "k0" => [{  }, ["two words", "x"]], "k1" => { "k0" => [-18] }, "k2" => { "k0" => "x" } } } }).inspect
puts sum_leaves({ "k3" => [{  }, { "k3" => ["x", -12, ["", -2, nil]], "k0" => [{ "k0" => "two words", "k1" => "two words" }, {  }, [-20, 0, "x", "x"]], "k2" => [], "k1" => -18 }, { "k1" => "", "k0" => -8 }, { "k0" => { "k0" => [], "k1" => [] }, "k3" => ["x", ["two words", -27, nil, ""]], "k2" => -12, "k1" => [nil, "x", nil] }], "k0" => [{ "k1" => "", "k2" => "two words", "k3" => 11, "k0" => nil }, { "k1" => [-30, ["two words"]], "k0" => { "k3" => [nil, nil, nil], "k0" => { "k1" => 26, "k0" => "" }, "k1" => "x", "k2" => "two words" }, "k3" => { "k0" => [8, nil, "", nil], "k1" => [""] }, "k2" => { "k0" => [], "k3" => ["x", ""], "k2" => {  }, "k1" => { "k0" => nil, "k2" => "two words", "k1" => "x" } } }, { "k1" => { "k0" => { "k1" => nil, "k2" => -7, "k0" => "two words" }, "k1" => ["two words", "", "two words"], "k2" => "" }, "k0" => { "k0" => [3, nil, "two words"], "k2" => [nil, "x"], "k1" => ["two words"] }, "k2" => {  } }, nil], "k1" => { "k0" => -2, "k1" => nil }, "k2" => 3 }).inspect
puts sum_leaves(["", [{  }, { "k0" => { "k0" => { "k0" => "x" }, "k2" => [], "k1" => { "k0" => "", "k1" => "two words" } }, "k1" => [[nil, "x", "", nil]], "k2" => { "k0" => nil } }], "two words", "two words"]).inspect
puts sum_leaves({ "k0" => "" }).inspect
puts sum_leaves([[-28, [], [[], "", [["two words"], "x", [], [6, "x"]]]], [[], { "k3" => { "k0" => ["two words", nil] }, "k2" => "two words", "k0" => [], "k1" => 27 }]]).inspect
