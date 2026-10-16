require_relative 'witness_support'
module Message; end
path = File.join(CAMPFIRE, 'app/models/message/attachment.rb')
nodes_in(path).grep(Prism::ConstantWriteNode).each do |node|
  next unless %i[THUMBNAIL_MAX_WIDTH THUMBNAIL_MAX_HEIGHT].include?(node.name)
  Message.const_set(node.name, eval(node.value.location.slice))
end
source_record(path, constants: [Message::THUMBNAIL_MAX_WIDTH, Message::THUMBNAIL_MAX_HEIGHT])
call_argument(File.join(CAMPFIRE, 'app/helpers/messages/attachment_presentation.rb'), 33, :preview, ['A001'])
finish('campfire-witnesses.json')
