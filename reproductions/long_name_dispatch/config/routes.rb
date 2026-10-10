Rails.application.routes.draw do
  resources :probes, only: :index
end
