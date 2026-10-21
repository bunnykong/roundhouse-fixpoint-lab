# Family: other. Row C1465 (Chatwoot).
#
# A WhatsApp contact message without contacts makes
# `Array(message_payload[:contacts]).first&.with_indifferent_access` evaluate to nil before the
# outer `|| {}` fallback. The candidate types this inner expression as HashWithIndifferentAccess
# only, which excludes nil.
require_relative 'support'

SERVICE = pinned('chatwoot', 'app/services/whatsapp/contact_info_response_service.rb',
                 '67efbc1edfcde59fc86f3082bc0a720b30a35887851bdb1c41d51a791a4e5f78')

# Boundary: the payload accessor returns a contact message with an empty contacts list.
service = Object.new
def service.message_payload = { contacts: [] }
# Row C1465 is the expression at line 37, bytes 852...916.
value = service.instance_eval(span(SERVICE, 852, 916), SERVICE, 37)

emit('C1465', value, app: 'chatwoot', path: 'app/services/whatsapp/contact_info_response_service.rb', line: 37,
     boundary: 'payload accessor returns {contacts: []}; expression unchanged')
