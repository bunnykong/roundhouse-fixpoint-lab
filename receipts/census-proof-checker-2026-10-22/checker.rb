# frozen_string_literal: true
#
# Independent source proof checker for F73's soundness census.
#
# For one narrowed row it either proves from the pinned application source that every runtime
# value at the row lies inside the candidate's type, or answers CANNOT_PROVE with a reason.
# The oracle is Prism (CRuby 4.0.7's parser) over the pinned source. The analyzer's dumps are used
# only to locate a row (source file, byte span, node kind) and to read the claimed type.
# Nothing from the analyzer or from the census tooling is imported or reused.
#
# Usage: APPS=DIR ruby checker.rb rows.jsonl verdicts.jsonl
# Each row names its source file relative to its app's checkout. APPS holds one checkout per app,
# at the lab's pinned commits; it defaults to the lab's corpus/apps (filled by `sh corpus/fetch.sh`).
#
# Trust base (documented assumptions, the same ones the hand proofs make):
#  - core literals build fresh objects of their core class; Array/Hash/String/Integer methods the
#    evaluator names (freeze, size, length, count, to_s on scalars, to_sym, +, -, *) are not redefined;
#  - is_a?/kind_of?/instance_of? are not redefined to lie; class arms are nominal (a subclass
#    instance is inside class{K}), as in the census's own HTTPFound check;
#  - no eval/binding/local_variable_set writes the locals of a scope (scopes that mention them are refused).
require "json"
require "prism"
require "digest"
require "set"

module ProofChecker
  # ---------------------------------------------------------------- abstract values
  # A value set is an Array of shapes (a union). Shapes:
  #   {k: :nil} {k: :true} {k: :false} {k: :int} {k: :float} {k: :str} {k: :sym}
  #   {k: :array, elem: VS} {k: :hash, key: VS, val: VS}  (contents are value sets; [] = none)
  #   {k: :inst, cls: "Name"}  (some object o with o.is_a?(Name))
  #   {k: :top, why: "..."}    (unknown)
  module V
    NIL = { k: :nil }.freeze
    TRUE_ = { k: :true }.freeze
    FALSE_ = { k: :false }.freeze
    INT = { k: :int }.freeze
    FLOAT = { k: :float }.freeze
    STR = { k: :str }.freeze
    SYM = { k: :sym }.freeze

    module_function

    def top(why) = [{ k: :top, why: why }]
    def top?(s) = s[:k] == :top
    def container?(s) = %i[array hash].include?(s[:k])

    def union(*sets)
      out = []
      sets.each { |set| set.each { |s| out << s unless out.include?(s) } }
      out
    end

    def falsy(vs)
      return [NIL, FALSE_] if vs.any? { |s| top?(s) || s[:k] == :inst }
      vs.select { |s| %i[nil false].include?(s[:k]) }
    end

    def truthy(vs) = vs.reject { |s| %i[nil false].include?(s[:k]) }

    # Contents of every container become unknown (the object escaped or was exposed).
    def opaque(s)
      case s[:k]
      when :array then { k: :array, elem: top("escaped contents") }
      when :hash then { k: :hash, key: top("escaped contents"), val: top("escaped contents") }
      else s
      end
    end

    # Containers nested inside s become opaque (elements were handed out and may be mutated).
    def expose(s)
      case s[:k]
      when :array then { k: :array, elem: s[:elem].map { |e| opaque(e) } }
      when :hash then { k: :hash, key: s[:key].map { |e| opaque(e) }, val: s[:val].map { |e| opaque(e) } }
      else s
      end
    end

    def show(vs)
      return "none" if vs.empty?
      vs.map { |s| show1(s) }.join(" | ")
    end

    def show1(s)
      case s[:k]
      when :array then "Array[#{show(s[:elem])}]"
      when :hash then "Hash[#{show(s[:key])}, #{show(s[:val])}]"
      when :inst then "is_a?(#{s[:cls]})"
      when :top then "?(#{s[:why]})"
      else s[:k].to_s
      end
    end

    def tops(vs, out = [])
      vs.each do |s|
        case s[:k]
        when :top then out << s[:why]
        when :array then tops(s[:elem], out)
        when :hash then tops(s[:key], out); tops(s[:val], out)
        end
      end
      out
    end
  end

  # ---------------------------------------------------------------- the row's type (analyzer JSON)
  # Membership follows the census's runtime-set relation: same kind required, untyped/var are top,
  # bottom admits nothing, an empty container is inside every container type of its kind.
  module T
    module_function

    def top_type?(t)
      case t["kind"]
      when "untyped", "var" then true
      when "union" then t["variants"].any? { |v| top_type?(v) }
      else false
      end
    end

    def arms(t) = t["kind"] == "union" ? t["variants"].flat_map { |v| arms(v) } : [t]

    def admits?(t, vs) = vs.all? { |s| admits1?(t, s) }

    def admits1?(t, s)
      return true if top_type?(t)
      return false if s[:k] == :top
      arms(t).any? { |a| arm?(a, s) }
    end

    def arm?(a, s)
      k = a["kind"]
      case s[:k]
      when :nil then k == "nil"
      when :true, :false then k == "bool"
      when :int then k == "int"
      when :float then k == "float"
      when :str then k == "str"
      when :sym then k == "sym"
      when :array then k == "array" && admits?(a["elem"], s[:elem])
      when :hash then k == "hash" && admits?(a["key"], s[:key]) && admits?(a["value"], s[:val])
      when :inst then k == "class" && a["id"] == s[:cls] && (a["args"] || []).all? { |x| top_type?(x) }
      else false
      end
    end

    def show(t)
      case t["kind"]
      when "union" then t["variants"].map { |v| show(v) }.join(" | ")
      when "array" then "Array[#{show(t['elem'])}]"
      when "hash" then "Hash[#{show(t['key'])}, #{show(t['value'])}]"
      when "class" then t["id"].to_s + (t["args"].to_a.empty? ? "" : "[#{t['args'].map { |x| show(x) }.join(', ')}]")
      when "relation" then "Relation[#{t['of']}]"
      else t["kind"].to_s
      end
    end
  end

  class CannotProve < StandardError; end

  # ---------------------------------------------------------------- one parsed source file
  class SourceFile
    SCOPES = %i[program_node def_node class_node module_node singleton_class_node block_node lambda_node].freeze
    WRITES = %i[local_variable_write_node local_variable_target_node local_variable_or_write_node
                local_variable_and_write_node local_variable_operator_write_node].freeze
    PARAMS = %i[required_parameter_node optional_parameter_node rest_parameter_node keyword_rest_parameter_node
                required_keyword_parameter_node optional_keyword_parameter_node block_parameter_node
                block_local_variable_node].freeze
    DYNAMIC = %i[binding eval local_variable_set instance_eval class_eval module_eval].freeze

    attr_reader :path, :text, :sha256, :root, :errors

    def initialize(path, text = nil)
      @path = path
      @text = text || File.binread(path)
      @sha256 = Digest::SHA256.hexdigest(@text)
      result = Prism.parse(@text, filepath: path.to_s)
      @errors = result.errors
      @root = result.value
      @parent = {}.compare_by_identity
      @scope_of = {}.compare_by_identity
      @var_of = {}.compare_by_identity
      @by_span = Hash.new { |h, k| h[k] = [] }
      @writes = Hash.new { |h, k| h[k] = [] }
      @reads = Hash.new { |h, k| h[k] = [] }
      @params = Hash.new { |h, k| h[k] = [] }
      @dynamic = Set.new.compare_by_identity
      index(@root, nil, [])
    end

    def parent(n) = @parent[n]
    def scope_of(n) = @scope_of[n]
    def var_of(n) = @var_of[n]
    def nodes_at(a, b) = @by_span.fetch([a, b], [])
    def writes(var) = @writes.fetch(var, [])
    def reads(var) = @reads.fetch(var, [])
    def params(var) = @params.fetch(var, [])
    def dynamic?(scope) = @dynamic.include?(scope)
    def line(offset) = @text.byteslice(0, offset).count("\n") + 1
    def snippet(n) = @text.byteslice(n.location.start_offset, n.location.end_offset - n.location.start_offset)

    def ancestors(n)
      out = []
      while (n = @parent[n])
        out << n
      end
      out
    end

    def inside?(n, outer)
      a, b = outer.location.start_offset, outer.location.end_offset
      n.location.start_offset >= a && n.location.end_offset <= b
    end

    private

    def var_key(scopes, depth, name)
      scope = scopes[-1 - depth]
      scope && [scope, name]
    end

    def index(node, parent, scopes)
      @parent[node] = parent if parent
      loc = node.location
      @by_span[[loc.start_offset, loc.end_offset]] << node
      @scope_of[node] = scopes.last
      case node.type
      when :local_variable_read_node
        if (v = var_key(scopes, node.depth, node.name))
          @var_of[node] = v
          @reads[v] << node
        end
      when *WRITES
        if (v = var_key(scopes, node.depth, node.name))
          @var_of[node] = v
          @writes[v] << node
        end
      when *PARAMS
        if node.name && scopes.last
          v = [scopes.last, node.name]
          @var_of[node] = v
          @params[v] << node
        end
      when :call_node
        @dynamic << scopes.last if DYNAMIC.include?(node.name) && scopes.last
      end
      # Children evaluated in the enclosing scope versus the new scope.
      outer, inner = [], []
      case node.type
      when :program_node
        inner = node.compact_child_nodes
      when :def_node
        outer = [node.receiver].compact
        inner = [node.parameters, node.body].compact
      when :class_node
        outer = [node.constant_path, node.superclass].compact
        inner = [node.body].compact
      when :module_node
        outer = [node.constant_path].compact
        inner = [node.body].compact
      when :singleton_class_node
        outer = [node.expression].compact
        inner = [node.body].compact
      when :block_node, :lambda_node
        inner = node.compact_child_nodes
      else
        outer = node.compact_child_nodes
      end
      outer.each { |c| index(c, node, scopes) }
      unless inner.empty?
        nested = scopes + [node]
        inner.each { |c| index(c, node, nested) }
      end
    end
  end

  # ---------------------------------------------------------------- constants defined by the app
  # Fully qualified names of every class, module and constant assignment in the app's Ruby files,
  # with the class/module kind. Used to resolve a guard's constant and to know it names a class.
  class ConstIndex
    def initialize(files)
      @kinds = {}
      @parents = Hash.new { |h, k| h[k] = [] } # class/module => superclass and included modules, as written
      files.each { |f| walk(f.root, []) }
    end

    def kind(name) = @kinds[name]
    def defined?(name) = @kinds.key?(name)

    # App-defined ancestors (superclasses and included modules), best effort, without the class itself.
    def ancestors(name, seen = Set.new)
      return [] unless seen.add?(name)
      @parents[name].flat_map do |(written, nesting)|
        full = resolve_written(written, nesting)
        full ? [full] + ancestors(full, seen) : []
      end
    end

    private

    def resolve_written(written, nesting)
      nesting.each do |ns|
        cand = "#{ns}::#{written}"
        return cand if @kinds.key?(cand)
      end
      @kinds.key?(written) ? written : nil
    end

    def path_name(n)
      case n&.type
      when :constant_read_node then n.name.to_s
      when :constant_path_node
        n.parent ? (p = path_name(n.parent)) && "#{p}::#{n.name}" : n.name.to_s
      end
    end

    def walk(n, nesting)
      case n.type
      when :class_node, :module_node
        rel = path_name(n.constant_path)
        if rel
          full = nesting.empty? ? rel : "#{nesting.last}::#{rel}"
          @kinds[full] = (@kinds[full] == :class || n.type == :class_node) ? :class : :module
          if n.type == :class_node && (sup = path_name(n.superclass))
            @parents[full] << [sup, nesting.reverse]
          end
          inner = nesting + [full]
          n.body&.compact_child_nodes&.each do |stmt|
            next unless stmt.type == :call_node && %i[include prepend].include?(stmt.name) && stmt.receiver.nil?
            (stmt.arguments&.arguments || []).each do |a|
              (w = path_name(a)) && @parents[full] << [w, inner.reverse]
            end
          end
          n.body && walk(n.body, inner)
          return
        end
      when :constant_write_node
        full = nesting.empty? ? n.name.to_s : "#{nesting.last}::#{n.name}"
        @kinds[full] ||= :value
      end
      n.compact_child_nodes.each { |c| walk(c, nesting) }
    end
  end

  # Core classes a guard may name (no app definition needed). Only these and app classes are
  # trusted as classes in `case x when K`; nil/false are dropped by a guard only for these.
  CORE_CLASSES = %w[Array Hash String Symbol Integer Float NilClass TrueClass FalseClass Numeric Proc
                    Time Date DateTime Regexp Range StandardError Exception].freeze

  # ---------------------------------------------------------------- the evaluator
  class Evaluator
    PURE = %i[size length count empty? any? none? key? has_key? include? member? nil? present? blank?
              is_a? kind_of? instance_of? frozen? == != eql? equal? hash inspect to_s to_json to_param
              respond_to? class positive? negative? zero? exists? exist?].freeze
    READERS = %i[[] fetch dig first last values keys each each_pair each_value each_key each_with_index
                 each_with_object map collect flat_map select filter reject find detect filter_map min max
                 min_by max_by sort sort_by group_by partition to_a to_h values_at slice except without compact
                 uniq flatten zip take drop sample shuffle reverse inject reduce sum tally index find_index dup
                 clone merge transform_values transform_keys join index_by index_with each_slice count
                 delete delete_if keep_if select! reject! filter! compact! uniq! sort! sort_by! reverse!
                 shuffle! rotate! shift pop slice! delete_at clear].freeze
    JUMPS = %i[return_node next_node break_node redo_node retry_node].freeze

    attr_reader :rules

    def initialize(file, consts)
      @f = file
      @consts = consts
      @rules = Set.new
      @active = Set.new
    end

    def rule(r) = @rules << r

    # Refuse rows whose subtree jumps out (return/next/break/redo/retry/throw), so that the row's
    # value is the node's own value under any reading of a body row.
    def refuse_jumps(n)
      # [node, inside a block/lambda/loop that owns next/break, inside a lambda that owns return]
      stack = [[n, false, false]]
      until stack.empty?
        x, owned, lam = stack.pop
        next if x.type == :def_node && !x.equal?(n)
        case x.type
        when :return_node then raise CannotProve, "return inside the row's expression" unless lam
        when :next_node, :break_node then raise CannotProve, "#{x.type} inside the row's expression" unless owned
        when :redo_node, :retry_node then raise CannotProve, "#{x.type} inside the row's expression"
        when :call_node
          raise CannotProve, "throw inside the row's expression" if x.name == :throw && x.receiver.nil?
        end
        o = owned || %i[block_node lambda_node while_node until_node for_node].include?(x.type)
        l = lam || x.type == :lambda_node
        x.compact_child_nodes.each { |c| stack << [c, o, l] }
      end
    end

    def ev(n)
      case n.type
      when :nil_node then [V::NIL]
      when :true_node then [V::TRUE_]
      when :false_node then [V::FALSE_]
      when :integer_node, :source_line_node then [V::INT]
      when :float_node then [V::FLOAT]
      when :string_node, :interpolated_string_node, :source_file_node then [V::STR]
      when :symbol_node, :interpolated_symbol_node then [V::SYM]
      when :array_node then ev_array(n)
      when :hash_node, :keyword_hash_node then ev_hash(n)
      when :parentheses_node then n.body ? ev(n.body) : [V::NIL]
      when :statements_node
        rule(:sequence) if n.body.size > 1
        n.body.empty? ? [V::NIL] : ev(n.body.last)
      when :begin_node then ev_begin(n)
      when :else_node then n.statements ? ev(n.statements) : [V::NIL]
      when :if_node
        rule(:branch)
        V.union(n.statements ? ev(n.statements) : [V::NIL], n.subsequent ? ev(n.subsequent) : [V::NIL])
      when :unless_node
        rule(:branch)
        V.union(n.statements ? ev(n.statements) : [V::NIL], n.else_clause ? ev(n.else_clause) : [V::NIL])
      when :case_node
        rule(:branch)
        whens = n.conditions.map { |w| w.statements ? ev(w.statements) : [V::NIL] }
        V.union(*whens, n.else_clause ? ev(n.else_clause) : [V::NIL])
      when :and_node then V.union(V.falsy(ev(n.left)), ev(n.right))
      when :or_node then V.union(V.truthy(ev(n.left)), ev(n.right))
      when :local_variable_write_node, :instance_variable_write_node, :class_variable_write_node,
           :global_variable_write_node, :constant_write_node, :constant_path_write_node
        rule(:assignment)
        ev(n.value)
      when :multi_write_node
        rule(:assignment)
        ev(n.value)
      when :local_variable_read_node then ev_local(n)
      when :call_node then ev_call(n)
      when :defined_node then [V::NIL, V::STR]
      when :return_node, :next_node, :break_node, :redo_node, :retry_node then [] # control leaves: no value here
      when :rescue_modifier_node then V.union(ev(n.expression), ev(n.rescue_expression))
      else V.top(n.type.to_s.delete_suffix("_node"))
      end
    end

    # Every value the method definition can return: its body's value when the body completes,
    # and the argument of every `return` that leaves this def (not a nested def or lambda).
    def return_values(defn)
      sets = [defn.body ? ev(defn.body) : [V::NIL]]
      stack = defn.body ? [defn.body] : []
      until stack.empty?
        x = stack.pop
        next if %i[def_node lambda_node].include?(x.type)
        if x.type == :return_node
          args = x.arguments ? x.arguments.arguments : []
          sets << if args.empty? then [V::NIL]
                  elsif args.size == 1 && args[0].type != :splat_node then ev(args[0])
                  else [{ k: :array, elem: V.union(*args.map { |a| a.type == :splat_node ? V.top("splat") : ev(a) }) }]
                  end
        end
        stack.concat(x.compact_child_nodes)
      end
      rule(:returns)
      V.union(*sets)
    end

    def ev_array(n)
      rule(n.elements.empty? ? :empty_literal : :literal)
      elems = n.elements.map do |e|
        e.type == :splat_node ? V.top("splat element") : ev(e)
      end
      [{ k: :array, elem: V.union(*elems) }]
    end

    def ev_hash(n)
      rule(n.elements.empty? ? :empty_literal : :literal)
      keys, vals = [], []
      n.elements.each do |e|
        if e.type == :assoc_node
          keys << ev(e.key)
          vals << (e.value.type == :implicit_node ? ev(e.value.value) : ev(e.value))
        else # **splat
          inner = e.value ? ev(e.value) : V.top("anonymous keyword splat")
          inner.each do |s|
            if s[:k] == :hash
              keys << s[:key]; vals << s[:val]
            elsif s[:k] != :nil
              keys << V.top("keyword splat"); vals << V.top("keyword splat")
            end
          end
        end
      end
      [{ k: :hash, key: V.union(*keys), val: V.union(*vals) }]
    end

    def ev_begin(n)
      main = n.else_clause ? ev(n.else_clause) : (n.statements ? ev(n.statements) : [V::NIL])
      sets = [main]
      r = n.rescue_clause
      while r
        rule(:branch)
        sets << (r.statements ? ev(r.statements) : [V::NIL])
        r = r.subsequent
      end
      V.union(*sets)
    end

    def args_of(call) = call.arguments ? call.arguments.arguments : []

    def plain_args?(call)
      args_of(call).none? { |a| %i[splat_node block_argument_node keyword_hash_node forwarding_arguments_node].include?(a.type) } &&
        !call.block.is_a?(Prism::BlockArgumentNode)
    end

    def ev_call(n)
      return [] if n.receiver.nil? && %i[raise fail].include?(n.name) # Kernel#raise never returns
      if n.attribute_write? # a.b = v and a[k] = v evaluate to v, whatever the setter returns
        raise CannotProve, "attribute write with splat or block arguments" unless plain_args?(n) && !args_of(n).empty?
        rule(:setter)
        v = ev(args_of(n).last)
        return n.safe_navigation? ? V.union(v, [V::NIL]) : v
      end
      return V.top("call #{n.name}") unless n.receiver && n.block.nil? && plain_args?(n)
      args = args_of(n)
      if %i[[] fetch].include?(n.name) && (args.size == 1 || (n.name == :fetch && args.size == 2))
        recv = ev(n.receiver)
        out = recv.flat_map { |s| element_read(s, args[0], n.name) }
        out = V.union(out, ev(args[1])) if args.size == 2
        rule(:element_read)
        return n.safe_navigation? ? V.union(out, [V::NIL]) : out
      end
      return V.top("call #{n.name}") unless args.empty?
      recv = ev(n.receiver)
      out = case n.name
            when :compact
              rule(:core_method)
              recv.map do |s|
                case s[:k]
                when :hash then { k: :hash, key: s[:key], val: s[:val].reject { |e| e[:k] == :nil } }
                when :array then { k: :array, elem: s[:elem].reject { |e| e[:k] == :nil } }
                else V.top("compact on #{V.show1(s)}")[0]
                end
              end
            when :freeze
              rule(:core_method)
              recv.map { |s| s[:k] == :inst ? V.top("freeze on #{s[:cls]}")[0] : s }
            when :size, :length
              rule(:core_method)
              sized?(recv) ? [V::INT] : V.top("#{n.name} on #{V.show(recv)}")
            when :to_s
              rule(:core_method)
              recv.all? { |s| %i[str sym int float nil true false].include?(s[:k]) } ? [V::STR] : V.top("to_s on #{V.show(recv)}")
            when :to_sym
              rule(:core_method)
              recv.all? { |s| %i[str sym].include?(s[:k]) } ? [V::SYM] : V.top("to_sym on #{V.show(recv)}")
            else
              return V.top("call #{n.name}")
            end
      n.safe_navigation? ? V.union(out, [V::NIL]) : out
    end

    def sized?(vs)
      vs.all? { |s| %i[array hash str].include?(s[:k]) || (s[:k] == :inst && %w[Array Hash String].include?(s[:cls])) }
    end

    # h[k] / h.fetch(k) on a literal-built Hash (no default) is a value or nil; a[i] with an Integer
    # index is an element or nil (a Range index would slice, so other indexes are unknown).
    def element_read(s, arg, name)
      case s[:k]
      when :nil then name == :[] ? V.top("[] on nil") : [] # nil[] raises: no value
      when :hash then name == :[] ? V.union(s[:val], [V::NIL]) : s[:val]
      when :array
        idx = ev(arg)
        return V.top("array index #{V.show(idx)}") unless idx.all? { |x| x[:k] == :int }
        name == :[] ? V.union(s[:elem], [V::NIL]) : s[:elem]
      when :str then name == :[] ? [V::STR, V::NIL] : V.top("fetch on String")
      else V.top("#{name} on #{V.show1(s)}")
      end
    end

    # ------------------------------------------------ locals: def-use, writers, escapes, guards
    def ev_local(read)
      var = @f.var_of(read)
      return V.top("unresolved local") unless var
      raise CannotProve, "scope uses eval/binding" if @f.dynamic?(var[0])
      return V.top("recursive local #{var[1]}") if @active.include?(var)
      rule(:local)
      @active << var
      begin
        if @f.params(var).any?
          vs = V.top("parameter #{var[1]}")
        else
          vs = local_values(var, read)
        end
        refine(vs, read, var)
      ensure
        @active.delete(var)
      end
    end

    def local_values(var, read)
      writes = @f.writes(var)
      vs = V.union(*writes.map { |w| write_value(w, var) })
      vs = V.union(vs, [V::NIL]) unless definitely_assigned?(read, var)
      apply_uses(vs, var, read)
    end

    def write_value(w, var)
      case w.type
      when :local_variable_write_node, :local_variable_or_write_node, :local_variable_and_write_node then ev(w.value)
      when :local_variable_operator_write_node
        base = @f.writes(var).reject { |x| x.type == :local_variable_operator_write_node }.flat_map { |x| write_value(x, var) }
        rhs = ev(w.value)
        op = w.binary_operator
        if %i[+ - *].include?(op) && (base + rhs).all? { |s| s[:k] == :int }
          [V::INT]
        elsif op == :+ && (base + rhs).all? { |s| s[:k] == :str }
          [V::STR]
        else
          V.top("operator write #{op}")
        end
      else V.top("#{w.type.to_s.delete_suffix('_node')} of #{var[1]}")
      end
    end

    def definitely_assigned?(read, var)
      node = read
      while (p = @f.parent(node)) && !p.equal?(var[0])
        if p.type == :statements_node
          i = p.body.index { |s| s.equal?(node) }
          return true if i && p.body[0...i].any? { |s| %i[local_variable_write_node local_variable_or_write_node].include?(s.type) && @f.var_of(s) == var }
        end
        node = p
      end
      false
    end

    # Fold the uses of the variable that may run before `at` into its container shapes: inserts add
    # keys and elements, `h[k] << v` and `h[k][j] = v` add to nested containers, other element reads
    # expose nested containers, and anything else (an argument, an alias, an unknown method) makes the
    # contents unknown. A use that can only run after `at` cannot change the value read at `at`.
    # PC_ABLATE_USES=1 disables this analysis; used only to show the negative control has teeth.
    ABLATE_USES = ENV["PC_ABLATE_USES"] == "1"

    def apply_uses(vs, var, at)
      return vs if ABLATE_USES
      return vs unless vs.any? { |s| V.container?(s) }
      keys, vals, elems = [], [], []
      nkeys, nvals, nelems = [], [], []
      escaped = exposed = false
      @f.reads(var).each do |r|
        next unless may_precede?(r, at, var)
        p = @f.parent(r)
        if p.type == :call_node && p.receiver.equal?(r)
          args = args_of(p)
          unless plain_args?(p)
            escaped = true
            next
          end
          exposed = true if p.block
          # These return the receiver itself: a used result is an alias.
          escaped = true if SELF_RETURNING.include?(p.name) && value_used?(p)
          case p.name
          when :[]=
            if args.size == 2
              keys << ev(args[0]); vals << ev(args[1])
            else
              escaped = true
            end
          when :<<, :push, :append, :unshift, :prepend
            args.each { |a| elems << ev(a) }
          when :insert
            args.drop(1).each { |a| elems << ev(a) }
          when :store
            args.size == 2 ? (keys << ev(args[0]); vals << ev(args[1])) : (escaped = true)
          when :merge!, :update
            escaped = true if p.block
            args.each do |a|
              ev(a).each { |s| s[:k] == :hash ? (keys << s[:key]; vals << s[:val]) : (escaped = true) }
            end
          when :concat
            args.each { |a| ev(a).each { |s| s[:k] == :array ? elems << s[:elem] : (escaped = true) } }
          when :[]
            g = @f.parent(p)
            if args.size == 1 && g&.type == :call_node && g.receiver.equal?(p) && g.block.nil? && plain_args?(g) &&
               %i[<< push append].include?(g.name)
              args_of(g).each { |a| nelems << ev(a) }
              exposed = true if value_used?(g)
            elsif args.size == 1 && g&.type == :call_node && g.receiver.equal?(p) && g.name == :[]= &&
                  plain_args?(g) && args_of(g).size == 2
              nkeys << ev(args_of(g)[0]); nvals << ev(args_of(g)[1])
            else
              exposed = true
            end
          when *PURE then nil
          when *READERS then exposed = true
          else escaped = true
          end
        elsif %i[index_or_write_node index_and_write_node].include?(p.type) && p.receiver.equal?(r)
          a = p.arguments ? p.arguments.arguments : []
          a.size == 1 ? (keys << ev(a[0]); vals << ev(p.value)) : (escaped = true)
          exposed = true
        elsif p.type == :index_operator_write_node && p.receiver.equal?(r)
          escaped = true
        elsif predicate_use?(r, p) || interpolated?(r, p)
          nil
        else
          escaped = true
        end
      end
      rule(:writers) unless [keys, vals, elems, nkeys, nvals, nelems].all?(&:empty?)
      nested = lambda do |e|
        case e[:k]
        when :array then { k: :array, elem: V.union(e[:elem], *nelems, *nvals) }
        when :hash then { k: :hash, key: V.union(e[:key], *nkeys), val: V.union(e[:val], *nvals) }
        else e
        end
      end
      vs.map do |s|
        next s unless V.container?(s)
        s = if escaped
              rule(:escaped)
              V.opaque(s)
            elsif s[:k] == :hash
              { k: :hash, key: V.union(s[:key], *keys), val: V.union(s[:val], *vals).map(&nested) }
            else
              { k: :array, elem: V.union(s[:elem], *vals, *elems).map(&nested) }
            end
        exposed ? V.expose(s) : s
      end
    end

    SELF_RETURNING = %i[<< push append unshift prepend insert concat merge! update each each_with_index each_pair
                        each_key each_value delete_if keep_if select! reject! filter! compact! uniq! sort! sort_by!
                        reverse! shuffle! rotate! clear to_a to_h].freeze

    # Whether the value of `n` can flow anywhere (conservative: anything but a discarded statement).
    def value_used?(n)
      p = @f.parent(n)
      case p&.type
      when :statements_node
        return false unless p.body.last.equal?(n)
        owner = @f.parent(p)
        case owner&.type
        when :if_node, :unless_node, :else_node, :when_node, :in_node, :case_node, :case_match_node,
             :begin_node, :parentheses_node, :ensure_node, :rescue_node
          owner.type == :ensure_node ? false : value_used?(%i[else_node when_node in_node rescue_node].include?(owner.type) ? @f.parent(owner) : owner)
        when :while_node, :until_node, :for_node, :class_node, :module_node, :singleton_class_node, :program_node then false
        when :block_node
          c = @f.parent(owner)
          !(c&.type == :call_node && c.block.equal?(owner) && DISCARDING.include?(c.name))
        else true
        end
      when :if_node, :unless_node then p.predicate.equal?(n) ? false : value_used?(p)
      when :while_node, :until_node then !p.predicate.equal?(n)
      else true
      end
    end

    # Core iterators that ignore the value their block returns.
    DISCARDING = %i[each each_with_index each_with_object each_pair each_key each_value each_slice each_cons
                    times upto downto step loop tap].freeze

    LOOPS = %i[while_node until_node for_node block_node lambda_node].freeze
    # Core iterators that call their block before returning and do not keep it.
    SYNC = %i[each each_with_index each_with_object each_pair each_key each_value each_slice each_cons map
              collect flat_map select filter reject filter_map find detect find_all partition group_by sort_by
              min_by max_by sum inject reduce count any? all? none? times upto downto step tap then
              index_by index_with loop].freeze

    def may_precede?(u, at, var)
      return reexecutable?(at, var) if u.equal?(at)
      !strictly_after?(u, at, var)
    end

    def reexecutable?(r, var)
      @f.ancestors(r).each do |a|
        break if a.equal?(var[0])
        return true if LOOPS.include?(a.type)
      end
      false
    end

    # u lies in a later statement than `at` of a statement list that runs once per activation of the
    # variable's scope, and `at` is not inside a closure that could be called after u.
    def strictly_after?(u, at, var)
      up = [u] + @f.ancestors(u)
      child_at = at
      @f.ancestors(at).each do |a|
        k = up.index { |x| x.equal?(a) }
        unless k
          child_at = a
          next
        end
        return false unless k >= 1
        if a.type == :statements_node
          i_at = a.body.index { |s| s.equal?(child_at) }
          i_u = a.body.index { |s| s.equal?(up[k - 1]) }
          return false unless i_at && i_u && i_at < i_u
        else
          # Two arms of one if/unless/case: only one runs per execution of the branch node.
          arm_at, arm_u = arm(a, child_at, at), arm(a, up[k - 1], u)
          return false unless arm_at && arm_u && !arm_at.equal?(arm_u)
        end
        @f.ancestors(a).each do |x|
          break if x.equal?(var[0])
          return false if LOOPS.include?(x.type)
        end
        x = at
        while (x = @f.parent(x)) && !x.equal?(a)
          return false if x.type == :lambda_node
          return false if x.type == :block_node && !sync_block?(x)
        end
        return true
      end
      false
    end

    # The arm of branch node `a` that holds `node` (reached through a's child `child`), or nil when
    # `node` sits in a's predicate or a's `when` conditions.
    def arm(a, child, node)
      case a.type
      when :if_node
        (child.equal?(a.statements) || child.equal?(a.subsequent)) ? child : nil
      when :unless_node
        (child.equal?(a.statements) || child.equal?(a.else_clause)) ? child : nil
      when :case_node
        if child.type == :when_node && a.conditions.any? { |w| w.equal?(child) }
          child.statements && (node.equal?(child.statements) || @f.ancestors(node).any? { |x| x.equal?(child.statements) }) ? child : nil
        elsif child.equal?(a.else_clause)
          child
        end
      end
    end

    def sync_block?(b)
      c = @f.parent(b)
      c&.type == :call_node && c.block.equal?(b) && SYNC.include?(c.name)
    end

    def predicate_use?(r, p)
      %i[if_node unless_node while_node until_node].include?(p.type) && p.predicate.equal?(r)
    end

    def interpolated?(r, p)
      p.type == :statements_node && @f.parent(p)&.type == :embedded_statements_node && p.body.size == 1
    end

    # ------------------------------------------------ dominating guards
    def refine(vs, read, var)
      facts = guard_facts(read, var)
      return vs if facts.empty?
      cls = facts.find { |f| f[0] == :cls }
      nonnil = facts.any? { |f| f[0] == :nonnil }
      rule(:guard)
      out = vs.flat_map do |s|
        if nonnil && %i[nil false].include?(s[:k]) then []
        elsif cls && V.top?(s) then [{ k: :inst, cls: cls[1] }]
        elsif cls && excluded_by_class?(s, cls[1]) then []
        else [s]
        end
      end
      V.union(out)
    end

    def excluded_by_class?(s, k)
      return false unless CORE_CLASSES.include?(k) || @consts.kind(k) == :class
      own = { nil: "NilClass", true: "TrueClass", false: "FalseClass", int: "Integer", float: "Float",
              str: "String", sym: "Symbol", array: "Array", hash: "Hash" }[s[:k]]
      return false unless own
      ok = [own, "Object", "BasicObject"]
      ok << "Numeric" if %i[int float].include?(s[:k])
      !ok.include?(k)
    end

    # Facts that hold at `read`, from dominating conditions on the same variable. A guard counts only
    # if no write to the variable can run after it: every write lies textually before the guard,
    # outside any closure, and outside any loop that contains the guard.
    def guard_facts(read, var)
      facts = []
      node = read
      while (p = @f.parent(node)) && !p.equal?(var[0])
        case p.type
        when :if_node
          if p.statements&.equal?(node) then facts += checked(p.predicate, var, true, p)
          elsif p.subsequent&.equal?(node) then facts += checked(p.predicate, var, false, p)
          end
        when :unless_node
          if p.statements&.equal?(node) then facts += checked(p.predicate, var, false, p)
          elsif p.else_clause&.equal?(node) then facts += checked(p.predicate, var, true, p)
          end
        when :and_node
          facts += checked(p.left, var, true, p) if p.right.equal?(node)
        when :or_node
          facts += checked(p.left, var, false, p) if p.right.equal?(node)
        when :when_node
          c = @f.parent(p)
          if c&.type == :case_node && p.statements&.equal?(node) && same_var?(c.predicate, var)
            ks = p.conditions.map { |x| class_const(x) }
            facts << [:cls, ks[0]] if ks.size == 1 && ks[0] && class_name?(ks[0]) && stable_after?(var, c)
          end
        when :statements_node
          i = p.body.index { |s| s.equal?(node) }
          p.body[0...i].each { |s| facts += early_exit_facts(s, var) } if i
        end
        node = p
      end
      facts
    end

    def checked(pred, var, truth, guard)
      return [] unless stable_after?(var, guard)
      truth ? facts_true(pred, var) : facts_false(pred, var)
    end

    def early_exit_facts(s, var)
      body = case s.type
             when :if_node then s.subsequent.nil? && s.statements
             when :unless_node then s.else_clause.nil? && s.statements
             end
      return [] unless body && body.body.size == 1 && exit?(body.body[0])
      return [] unless stable_after?(var, s)
      s.type == :if_node ? facts_false(s.predicate, var) : facts_true(s.predicate, var)
    end

    def exit?(x)
      %i[return_node next_node break_node].include?(x.type) ||
        (x.type == :call_node && x.receiver.nil? && %i[raise fail].include?(x.name))
    end

    def stable_after?(var, guard)
      g = guard.location.start_offset
      @f.writes(var).all? do |w|
        w.location.end_offset <= g && !in_closure_or_loop?(w, var, guard)
      end
    end

    def in_closure_or_loop?(w, var, guard)
      @f.ancestors(w).each do |a|
        break if a.equal?(var[0])
        return true if %i[block_node lambda_node].include?(a.type)
        return true if %i[while_node until_node for_node].include?(a.type) && @f.inside?(guard, a)
      end
      false
    end

    def same_var?(x, var) = x&.type == :local_variable_read_node && @f.var_of(x) == var

    def facts_true(pred, var)
      case pred.type
      when :parentheses_node
        pred.body&.type == :statements_node && pred.body.body.size == 1 ? facts_true(pred.body.body[0], var) : []
      when :and_node then facts_true(pred.left, var) + facts_true(pred.right, var)
      when :local_variable_read_node then same_var?(pred, var) ? [[:nonnil]] : []
      when :call_node
        if pred.name == :! && pred.receiver && args_of(pred).empty?
          facts_false(pred.receiver, var)
        elsif %i[is_a? kind_of? instance_of?].include?(pred.name) && same_var?(pred.receiver, var) && args_of(pred).size == 1
          k = class_const(args_of(pred)[0])
          k ? [[:cls, k]] : []
        elsif pred.name == :present? && same_var?(pred.receiver, var) && args_of(pred).empty?
          [[:nonnil]]
        else
          []
        end
      else []
      end
    end

    def facts_false(pred, var)
      case pred.type
      when :parentheses_node
        pred.body&.type == :statements_node && pred.body.body.size == 1 ? facts_false(pred.body.body[0], var) : []
      when :or_node then facts_false(pred.left, var) + facts_false(pred.right, var)
      when :call_node
        if pred.name == :! && pred.receiver && args_of(pred).empty?
          facts_true(pred.receiver, var)
        elsif %i[nil? blank?].include?(pred.name) && same_var?(pred.receiver, var) && args_of(pred).empty?
          [[:nonnil]]
        else
          []
        end
      else []
      end
    end

    # Resolve a guard's constant to a fully qualified name the way Ruby does: the lexical scopes
    # first, then the ancestors of the innermost class, then the top level. An app-defined ancestor
    # constant of the same name refuses the guard instead of guessing the method resolution order.
    def class_const(c)
      parts = const_parts(c)
      return nil unless parts
      absolute, names = parts
      return names.join("::") if absolute
      nesting = lexical_nesting(c)
      return nil unless nesting
      nesting.each do |ns|
        cand = "#{ns}::#{names[0]}"
        return ([cand] + names.drop(1)).join("::") if @consts.defined?(cand)
      end
      unless nesting.empty?
        return nil if @consts.ancestors(nesting[0]).any? { |s| @consts.defined?("#{s}::#{names[0]}") }
      end
      names.join("::")
    end

    def const_parts(c)
      case c&.type
      when :constant_read_node then [false, [c.name.to_s]]
      when :constant_path_node
        if c.parent.nil? then [true, [c.name.to_s]]
        elsif (p = const_parts(c.parent)) then [p[0], p[1] + [c.name.to_s]]
        end
      end
    end

    # Innermost first. A compact `class A::B` opens only A::B, not A.
    def lexical_nesting(n)
      out = []
      @f.ancestors(n).each do |a|
        next unless %i[class_node module_node].include?(a.type)
        parts = const_parts(a.constant_path)
        return nil unless parts
        out << parts[1].join("::")
      end
      # Qualify each entry by the entries outside it.
      full = []
      out.reverse.each { |name| full << (full.empty? ? name : "#{full.last}::#{name}") }
      full.reverse
    end

    def class_name?(k) = CORE_CLASSES.include?(k) || @consts.kind(k) == :class
  end

  # ---------------------------------------------------------------- rows
  # Dump node kind -> Prism node types whose value is the row's value.
  COMPAT = {
    "Hash" => %i[hash_node keyword_hash_node],
    "Array" => %i[array_node],
    "Assign" => %i[local_variable_write_node instance_variable_write_node class_variable_write_node
                   global_variable_write_node constant_write_node constant_path_write_node],
    "MultiAssign" => %i[multi_write_node],
    "Send" => %i[call_node],
    "Seq" => %i[statements_node parentheses_node],
    "If" => %i[if_node unless_node],
    "Case" => %i[case_node],
    "Var" => %i[local_variable_read_node],
    "BoolOp" => %i[and_node or_node],
    "BeginRescue" => %i[begin_node]
  }.freeze

  class Checker
    def initialize(app_roots)
      @app_roots = app_roots
      @files = {}
      @consts = {}
    end

    def file(path) = (@files[path] ||= SourceFile.new(path))

    def consts(app)
      @consts[app] ||= begin
        root = @app_roots.fetch(app)
        files = Dir.glob(File.join(root, "{app,lib,config}", "**", "*.rb")).sort.map { |p| file(p) }
        ConstIndex.new(files)
      end
    end

    def check(row)
      base = { "id" => row["id"], "verdict" => "CANNOT_PROVE", "pattern" => nil }
      begin
        base.merge(prove(row))
      rescue CannotProve => e
        base.merge("reason" => e.message)
      end
    end

    def prove(row)
      table, node_kind = row["table"], row["node"]
      return prove_returns(row) if table == "returns"
      raise CannotProve, "#{table} row: no source expression (pattern not implemented)" unless %w[ir controller_cache].include?(table)
      raise CannotProve, "#{table} binding row: ivar writer enumeration not implemented" if row["key"].to_s.include?(":binding:")
      src, span = row["source"], row["span"]
      raise CannotProve, "synthetic IR node without a source span" unless src.is_a?(String) && span && span["end"].to_i > span["start"].to_i
      kinds = COMPAT[node_kind]
      raise CannotProve, "dump node kind #{node_kind} has no checked counterpart" unless kinds
      if RUBY_FILES.include?(File.extname(src))
        f = file(src)
        raise CannotProve, "Prism parse errors in #{File.basename(src)}" unless f.errors.empty?
        nodes = f.nodes_at(span["start"], span["end"]).select { |n| kinds.include?(n.type) }
        sha, line = f.sha256, nil
      else
        f, nodes, sha, line = template_snippet(src, span, kinds)
      end
      raise CannotProve, "no #{kinds.join('/')} node at the span" if nodes.empty?
      type = row["candidate"]
      results = nodes.map do |n|
        ev = Evaluator.new(f, consts(row["app"]))
        ev.refuse_jumps(n)
        vs = ev.ev(n)
        unless T.admits?(type, vs)
          why = V.tops(vs)
          raise CannotProve, (why.empty? ? "value #{V.show(vs)} outside #{T.show(type)}" : "unknown: #{why.uniq.first(3).join('; ')}")
        end
        [n, vs, ev.rules]
      end
      n, vs, rules = results.first
      {
        "verdict" => "PROVED",
        "pattern" => pattern(vs, rules),
        "rules" => results.flat_map { |r| r[2].to_a }.uniq.map(&:to_s).sort,
        "prism_node" => results.map { |r| r[0].type.to_s }.join("+"),
        "value" => V.show(vs),
        "type" => T.show(type),
        "file" => src,
        "file_sha256" => sha,
        "line" => line || f.line(n.location.start_offset)
      }
    end

    RUBY_FILES = %w[.rb .jbuilder .rake .ru].freeze

    # ERB/Haml: the span's text is parsed on its own, without the template's context, so only
    # context-free expressions can be proved (an identifier parses as a method call: unknown).
    def template_snippet(src, span, kinds)
      text = File.binread(src)
      a, b = span["start"], span["end"]
      snippet = text.byteslice(a, b - a)
      len = snippet.bytesize
      sha = Digest::SHA256.hexdigest(text)
      line = text.byteslice(0, a).count("\n") + 1
      f = SourceFile.new("#{src}@#{a}", snippet)
      if f.errors.empty?
        stmts = f.root.statements.body
        if stmts.size == 1 && stmts[0].location.start_offset.zero? && stmts[0].location.end_offset == len &&
           kinds.include?(stmts[0].type)
          return [f, [stmts[0]], sha, line]
        end
      end
      wrapped = SourceFile.new("#{src}@#{a}", "__pc__(#{snippet})")
      if wrapped.errors.empty?
        call = wrapped.root.statements.body[0]
        args = call&.type == :call_node && call.arguments ? call.arguments.arguments : []
        if args.size == 1 && args[0].location.start_offset == 7 && args[0].location.end_offset == 7 + len &&
           kinds.include?(args[0].type)
          return [wrapped, [args[0]], sha, line]
        end
      end
      raise CannotProve, "template span is not one standalone #{kinds.join('/')} expression"
    end

    # A returns row C#m / C.m: the union over every `def` the app writes for that owner and name.
    # Several definitions (reopened classes) are joined, which covers whichever one is loaded last.
    def prove_returns(row)
      defs = methods(row["app"]).fetch(row["key"], [])
      raise CannotProve, "returns row: no `def` for #{row['key']} in the app (inherited, generated or mixed in)" if defs.empty?
      type = row["candidate"]
      sets, rules = [], Set.new
      defs.each do |f, d|
        ev = Evaluator.new(f, consts(row["app"]))
        sets << ev.return_values(d)
        rules.merge(ev.rules)
      end
      vs = V.union(*sets)
      unless T.admits?(type, vs)
        why = V.tops(vs)
        raise CannotProve, (why.empty? ? "returns #{V.show(vs)} outside #{T.show(type)}" : "unknown: #{why.uniq.first(3).join('; ')}")
      end
      f, d = defs.first
      { "verdict" => "PROVED", "pattern" => pattern(vs, rules), "rules" => rules.map(&:to_s).sort,
        "prism_node" => "def_node", "value" => V.show(vs), "type" => T.show(type), "file" => f.path,
        "file_sha256" => f.sha256, "line" => f.line(d.location.start_offset), "defs" => defs.size }
    end

    APP_DIRS = "{app,lib,config,db,test,spec,enterprise}".freeze

    # "Owner#name" / "Owner.name" => [[file, def_node], ...] over the app's Ruby files.
    def methods(app)
      @methods ||= {}
      @methods[app] ||= begin
        index = Hash.new { |h, k| h[k] = [] }
        Dir.glob(File.join(@app_roots.fetch(app), APP_DIRS, "**", "*.rb")).sort.each do |p|
          f = file(p)
          next unless f.errors.empty?
          collect_defs(f, f.root, [], false, index)
        end
        index
      end
    end

    def const_name(n)
      case n&.type
      when :constant_read_node then n.name.to_s
      when :constant_path_node then n.parent ? (p = const_name(n.parent)) && "#{p}::#{n.name}" : n.name.to_s
      end
    end

    def collect_defs(f, n, nesting, singleton, index)
      case n.type
      when :class_node, :module_node
        rel = const_name(n.constant_path)
        return unless rel
        full = nesting.empty? ? rel : "#{nesting.last}::#{rel}"
        n.body && collect_defs(f, n.body, nesting + [full], false, index)
        return
      when :singleton_class_node
        n.body && collect_defs(f, n.body, nesting, n.expression.type == :self_node, index) if n.expression.type == :self_node
        return
      when :def_node
        owner = nesting.last
        if owner
          if n.receiver.nil?
            index["#{owner}#{singleton ? '.' : '#'}#{n.name}"] << [f, n]
          elsif n.receiver.type == :self_node
            index["#{owner}.#{n.name}"] << [f, n]
          end
        end
        return
      end
      n.compact_child_nodes.each { |c| collect_defs(f, c, nesting, singleton, index) }
    end

    def pattern(vs, rules)
      return "exhaustive returns" if rules.include?(:returns)
      return "dominating guard" if rules.include?(:guard)
      nonempty = vs.any? { |s| V.container?(s) && ((s[:k] == :array && !s[:elem].empty?) || (s[:k] == :hash && !s[:key].empty?)) }
      return "fixed key schema" if nonempty
      return "fresh constructor" if vs.any? { |s| V.container?(s) }
      "literal"
    end
  end

  def self.main(argv)
    rows_path, out_path = argv
    apps = ENV.fetch("APPS", File.expand_path("../../corpus/apps", __dir__))
    rows = File.readlines(rows_path).map { |l| JSON.parse(l) }
    roots = rows.map { |r| r["app"] }.uniq.to_h { |a| [a, File.join(apps, a)] }
    roots.each_value { |d| raise "no app checkout at #{d}; run `sh corpus/fetch.sh` or set APPS" unless Dir.exist?(d) }
    checker = Checker.new(roots)
    File.open(out_path, "w") do |out|
      rows.each do |r|
        root = roots.fetch(r["app"])
        r = r.merge("source" => File.join(root, r["source"])) if r["source"].is_a?(String)
        v = checker.check(r)
        v["file"] = v["file"].delete_prefix("#{root}/") if v["file"]
        out.puts(JSON.generate(v))
      end
    end
  end
end

ProofChecker.main(ARGV) if $PROGRAM_NAME == __FILE__
