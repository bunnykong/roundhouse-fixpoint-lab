#!/bin/sh
# Run the CRuby and ActionPack witnesses on the repros and compare them with recorded.txt.
# RUBY is CRuby 4.0.7 (default `ruby`). RAILS_RUBY is a Ruby with the actionpack and actionview 8.1.4 gems
# (default `ruby`); the recording used Ruby 3.3.2, since 4.0.7 had no Rails gems installed.
set -eu
cd "$(dirname "$0")/.."
RUBY=${RUBY:-ruby}
RAILS_RUBY=${RAILS_RUBY:-ruby}
OUT=$(mktemp)
trap 'rm -f "$OUT"' EXIT
{
  for v in as-written swapped; do
    echo "== 2-ivar-index-write $v"
    $RUBY witness/cruby_witness.rb "repros/2-ivar-index-write/$v" 'Bag.new.t' 'b = Bag.new; b.reset; b.put; b.t' \
      'Bag.new.tap(&:reset).put'
  done
  for p in 5-model-files 6-split-model; do
    for v in as-written swapped; do
      echo "== $p $v"
      $RUBY witness/cruby_witness.rb "repros/$p/$v" 'XController.new.show'
    done
  done
  for v in as-written swapped; do
    echo "== 7-helper-method $v"
    $RAILS_RUBY witness/rails_witness.rb "repros/7-helper-method/$v" AController BController
  done
  for v in as-written swapped; do
    echo "== 9-filter-ivars $v"
    $RAILS_RUBY witness/rails_witness.rb "repros/9-filter-ivars/$v" PController
  done
} > "$OUT"
diff witness/recorded.txt "$OUT"
echo "the witnesses match witness/recorded.txt"
