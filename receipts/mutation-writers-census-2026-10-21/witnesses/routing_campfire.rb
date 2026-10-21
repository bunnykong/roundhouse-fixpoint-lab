# Family: routing or missing contribution. Rows A010, A013 and A014 (Campfire).
#
# SessionsController and UsersController declare `only: %i[ new create ]`. Authentication forwards
# those options to the callback registrars. Ruby binds `options` to {only: [:new, :create]};
# the candidate types `options` as Hash[Bottom, Bottom], which admits only an empty Hash.
require_relative 'support'

AUTH = pinned('campfire', 'app/controllers/concerns/authentication.rb',
              '8608d2cfe51ef299b5ac2d1a17f838871bc161ea087082d629d92b9e74b89fc9')
SESSIONS = pinned('campfire', 'app/controllers/sessions_controller.rb',
                  '5d334510b97e7aac8648df25eeae067d0f26968d7a0eca66e0f9396bbf38023c')
USERS = pinned('campfire', 'app/controllers/users_controller.rb',
               '1a9c9bf2db9087d101b8d5fe08a49b3505db7c8104c94ad242804e9f65359bf8')

# Boundary: the Rails callback registrars only receive their arguments.
controller = Object.new
def controller.skip_before_action(*, **) = nil
def controller.before_action(*, **) = nil
install(controller.singleton_class, AUTH, :allow_unauthenticated_access)
install(controller.singleton_class, AUTH, :require_unauthenticated_access)

seen = {}
trace = TracePoint.new(:line) do |tp|
  seen[tp.lineno] = tp.binding.local_variable_get(:options) if tp.path == AUTH && [15, 24].include?(tp.lineno)
end
trace.enable do
  controller.instance_eval(File.readlines(SESSIONS)[1], SESSIONS, 2)
  controller.instance_eval(File.readlines(USERS)[1], USERS, 2)
end

boundary = 'callback registrars record their arguments; declarations and methods unchanged'
path = 'app/controllers/concerns/authentication.rb'
emit('A010', seen.fetch(15), app: 'campfire', path: path, line: 15, boundary: boundary)
emit('A013', seen.fetch(24), app: 'campfire', path: path, line: 24, boundary: boundary)
emit('A014', seen.fetch(24), app: 'campfire', path: path, line: 24, boundary: boundary)
