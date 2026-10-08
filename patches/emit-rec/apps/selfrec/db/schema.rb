ActiveRecord::Schema[8.0].define(version: 1) do
  # One unrelated table: the Crystal target only emits `Schema` when a table exists.
  create_table "notes", force: :cascade do |t|
    t.string "body"
  end
end
