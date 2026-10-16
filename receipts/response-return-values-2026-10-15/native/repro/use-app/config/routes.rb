Rails.application.routes.draw do
  resources :uses, only: [:create, :show, :update]
end
