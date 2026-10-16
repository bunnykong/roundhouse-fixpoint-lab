Rails.application.routes.draw do
  get "widgets/:id", to: "widgets#show"
end
