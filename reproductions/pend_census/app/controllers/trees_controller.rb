class TreesController < ApplicationController
  def index
    s = Source.new({ "limit" => 5 })
    xs = [1, 2]
    @tree = [s.ivar_reflective, s.ivar_get, s.named_capture("x12"), s.for_var(xs), s.slice_param(xs),
             s.zip_param(xs), s.inject_acc(xs), s.ewo_param(xs), s.loop_break, s.catch_value, s.enum_value,
             s.via_missing, s.defined_dyn, s.aliased, s.ivar_reflective_len, s.named_capture_len("x12"),
             s.loop_break_len, s.via_missing_len, Kid.new.doubled(5)]
  end
end
