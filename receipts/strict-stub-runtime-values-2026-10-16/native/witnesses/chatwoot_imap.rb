#!/usr/bin/env ruby
# CRuby witnesses using pinned Chatwoot bodies and a real net-imap client.
# The local fixture server supplies protocol responses; there is no Rails boot.
require_relative 'boundary_tools'
require 'socket'
require 'base64'
require 'timeout'
require 'net/imap'

TASK = File.expand_path(ENV.fetch('WITNESS_VENDOR'))
$LOAD_PATH.unshift(File.join(TASK, 'concurrent-ruby-1.3.8/lib/concurrent-ruby'))
$LOAD_PATH.unshift(File.join(TASK, 'activesupport-7.2.3.1/lib'))
require 'active_support/core_ext/object/blank'

raise 'wrong net-imap pin' unless Gem.loaded_specs.fetch('net-imap').version.to_s == '0.6.4.1'
AUTH = File.join(INPUTS, 'chatwoot/app/services/imap/authentication.rb')
HELPER = File.join(INPUTS, 'chatwoot/app/helpers/api/v1/inboxes_helper.rb')
module Imap; end
load AUTH
SOURCES << { path: AUTH, sha256: Digest::SHA256.file(AUTH).hexdigest, extraction: 'entire unchanged module' }

class InboxesBoundary
end
%i[build_imap_connection open_imap_connection].each do |name|
  install_method(InboxesBoundary, HELPER, name)
end

EVENTS = []
SESSIONS = []
CURRENT = {}

def snapshot(value)
  if value.is_a?(Net::IMAP::TaggedResponse)
    { ruby_class: value.class.name, value: value.to_h, ancestors: value.class.ancestors.map(&:name).compact }
  elsif value.is_a?(Net::IMAP)
    { ruby_class: value.class.name, value: 'live local IMAP client',
      ancestors: value.class.ancestors.map(&:name).compact }
  else
    { ruby_class: value.class.name, value: value,
      ancestors: value.class.ancestors.map(&:name).compact }
  end
end

trace = TracePoint.new(:call, :return, :line) do |tp|
  next unless tp.path == AUTH && tp.method_id == :authenticate!
  event = { witness: CURRENT[:label], event: tp.event, line: tp.lineno, method: tp.method_id }
  if tp.binding.local_variable_defined?(:imap)
    event[:imap] = snapshot(tp.binding.local_variable_get(:imap))
  end
  event[:returned] = snapshot(tp.return_value) if tp.event == :return
  EVENTS << event
end

def with_imap_server(label)
  server = TCPServer.new('127.0.0.1', 0)
  port = server.local_address.ip_port
  exchange = []
  worker = Thread.new do
    socket = server.accept
    socket.write("* OK [CAPABILITY IMAP4rev1 AUTH=PLAIN AUTH=CRAM-MD5] witness-ready\r\n")
    while (line = socket.gets)
      exchange << { from: 'client', line: line.strip }
      tag, command, rest = line.strip.split(' ', 3)
      case command
      when 'CAPABILITY'
        socket.write("* CAPABILITY IMAP4rev1 AUTH=PLAIN AUTH=CRAM-MD5\r\n#{tag} OK capabilities\r\n")
      when 'LOGIN'
        socket.write("#{tag} OK authenticated\r\n")
      when 'AUTHENTICATE'
        challenge = rest == 'CRAM-MD5' ? Base64.strict_encode64('<witness.challenge@example.test>') : ''
        socket.write("+ #{challenge}\r\n")
        response = socket.gets
        raise 'missing SASL response' unless response
        exchange << { from: 'client', line: response.strip }
        socket.write("#{tag} OK authenticated\r\n")
      when 'LOGOUT'
        socket.write("* BYE witness-complete\r\n#{tag} OK logout\r\n")
        break
      else
        raise "Unexpected protocol command #{line.inspect}"
      end
    end
  ensure
    socket&.close
  end
  client = nil
  result = Timeout.timeout(10) do
    value = yield(port, ->(c) { client = c })
    client.disconnect if client && !client.disconnected?
    worker.value
    value
  end
  SESSIONS << { label: label, protocol: exchange }
  result
ensure
  client&.disconnect unless client&.disconnected?
  server&.close
  worker&.kill if worker&.alive?
end

trace.enable do
  ['cram-md5', 'login', 'plain', nil, ''].each do |mechanism|
    label = "authenticate!/mechanism=#{mechanism.inspect}"
    CURRENT[:label] = label
    result = with_imap_server(label) do |port, remember|
      imap = Net::IMAP.new('127.0.0.1', port: port, ssl: false)
      remember.call(imap)
      observe(label + '/receiver', imap, Net::IMAP)
      value = Imap::Authentication.authenticate!(imap, mechanism, 'witness-user', 'witness-password')
      observe(label + '/return', value, Net::IMAP::TaggedResponse)
      value
    end
    raise 'expected successful authentication' unless result.name == 'OK'
  end

  label = 'open_imap_connection/helper-path'
  CURRENT[:label] = label
  with_imap_server(label) do |port, remember|
    # Record the actual constructor used by the unmodified helper, without replacing its result.
    constructor_trace = TracePoint.new(:return) do |tp|
      if tp.path == HELPER && tp.method_id == :build_imap_connection
        remember.call(tp.return_value)
      end
    end
    value = constructor_trace.enable do
      InboxesBoundary.new.open_imap_connection(
        { imap_address: '127.0.0.1', imap_port: port, imap_enable_ssl: false,
          imap_login: 'witness-user', imap_password: 'witness-password' }, 'login')
    end
    observe(label + '/return', value, Net::IMAP)
    value
  end
end

loaded = $LOADED_FEATURES.select do |path|
  path.include?('/net-imap-0.6.4.1/') || path.include?('/active_support/core_ext/object/blank.rb') ||
    path.include?('/concurrent-ruby-1.3.8/')
end
payload = {
  condition: 'strict-stub-runtime-witnesses-20261016-chatwoot-cruby407', ruby: RUBY_DESCRIPTION,
  app_pin: '9f920b549c14491a4e587687a3eed5d21c6ccc7d',
  net_imap: Gem.loaded_specs.fetch('net-imap').version.to_s,
  active_support: '7.2.3.1', concurrent_ruby: '1.3.8',
  scope: 'Unmodified app bodies; pinned library code; local successful IMAP protocol fixture; no full Rails boot.',
  sources: SOURCES,
  loaded_sources: loaded.map { |p| { path: p, sha256: Digest::SHA256.file(p).hexdigest } },
  observations: OBSERVATIONS.map { |r| r.merge(value: snapshot(r[:value])[:value]) },
  events: EVENTS, sessions: SESSIONS
}
puts JSON.pretty_generate(payload)
