# CRuby witness for the Hash branch the strict guard removes from the inferred page type.
#
# JsonLdHelper#fetch_collection_page returns its argument unchanged when it is a Hash.
# With the guard, the inferred return is `Unresolved | nil`; Unresolved admits every value,
# so dropping the explicit `Hash[Unresolved, Unresolved]` arm excludes no Hash.
# Needs CRuby 4.0.7 and the pinned Mastodon source (APPS, default corpus/apps).
require 'digest'
require 'json'
require 'prism'

abort "CRuby 4.0.7 required; this is #{RUBY_DESCRIPTION}" unless RUBY_ENGINE == 'ruby' && RUBY_VERSION == '4.0.7'

apps = ENV.fetch('APPS', File.expand_path('../../corpus/apps', __dir__))
file = File.join(apps, 'mastodon', 'app/helpers/json_ld_helper.rb')
sha256 = 'b007ac30fe67a49e0ac0ee7b7b1fbcc03449b785ff8eb8fdc381f0d1f3bdc1cc'
abort "missing #{file}; set APPS to a directory of pinned app checkouts" unless File.file?(file)
abort "#{file}: unexpected SHA-256" unless Digest::SHA256.file(file).hexdigest == sha256

# Install the complete, unchanged method at its own file name and line numbers.
found = []
queue = [Prism.parse_file(file).value]
while (node = queue.shift)
  found << node if node.is_a?(Prism::DefNode) && node.name == :fetch_collection_page
  queue.concat(node.compact_child_nodes)
end
abort "expected one definition, found #{found.size}" unless found.size == 1
helper = Object.new
helper.singleton_class.module_eval(found.first.location.slice, file, found.first.location.start_line)

pages = [
  { 'type' => 'OrderedCollectionPage', 'orderedItems' => [] },
  { 'next' => { 'items' => [] } },
  { 'id' => 'https://example.test/featured', 'first' => 'https://example.test/featured?page=1' },
]
pages.each do |page|
  result = helper.fetch_collection_page(page)
  abort 'the Hash branch did not return its argument' unless result.equal?(page)
  puts JSON.generate(ruby: RUBY_DESCRIPTION, line: found.first.location.start_line + 1,
                     ruby_class: result.class.name, same_object: true, keys: result.keys)
end
