Rails.application.routes.draw do
  post "/notes", to: "notes#create"
end
