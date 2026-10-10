# Supplemental probe of actual object cycles, separate from finite recursive JSON trees.
a = []
a << a
puts a.equal?(a[0])
puts a.inspect
h = {}
h["self"] = h
puts h.equal?(h["self"])
puts h.inspect
