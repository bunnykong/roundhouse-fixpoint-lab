ActiveRecord::Schema[8.0].define(version: 1) do
  create_table "widgets", force: :cascade do |t|
    t.string "name"
    t.json "prefs"
  end
end
