class Probe
  # A method name longer than 80 bytes, reached by send with a String literal.
  def value_read_through_send_with_a_string_literal_longer_than_the_eighty_character_name_scan_limit = Chain.first_link(1)
  def reader = send("value_read_through_send_with_a_string_literal_longer_than_the_eighty_character_name_scan_limit")
end
