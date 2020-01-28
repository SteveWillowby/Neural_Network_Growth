

BF_POS_LIT = 1
BF_NEG_LIT = 2
BF_AND = 3
BF_OR = 4
BF_NOT = 5

class BooleanFormula:

    def __init__(self, t, values, identifier):
        self.type = t
        self.sub_formulae = values
        self.id = identifier

    def set_id(self, identifier):
        self.id = identifier

    def get_id(self):
        return self.id

    def get_type(self):
        return self.type

    def get_contents(self):
        return list(self.sub_formulae) # TODO: Consider whether removing the copy for the sake of efficiency is worthwhile

    def get_actual_contents(self):
        return self.sub_formulae

    def to_string(self, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")", with_spaces=False):
        if self.type == BF_POS_LIT:
            return str(self.sub_formulae[0])
        if self.type == BF_NEG_LIT:
            return "".join([not_str, str(self.sub_formulae[0])])
        if self.type == BF_NOT:
            return "".join([not_str, self.sub_formulae[0].to_string(and_str, or_str, not_str, left_par_str, right_par_str, with_spaces)])

        divider = and_str
        if self.type == BF_OR:
            divider = or_str
        if with_spaces:
            divider = "".join([" ", divider, " "])
        strs = [divider for i in range(0, len(self.sub_formulae) * 2 + 1)]
        strs[0] = left_par_str
        strs[-1] = right_par_str
        for i in range(0, len(self.sub_formulae)):
            strs[1 + 2*i] = self.sub_formulae[i].to_string(and_str, or_str, not_str, left_par_str, right_par_str, with_spaces)
        return "".join(strs)
        

class BooleanFormulaeBank:

    def __init__(self):
        self.next_numeric_id = 1
        self.tuple_id_to_numeric_id = {}
        self.id_to_formula = {}
        self.id_to_containing_ids = {}

    # Given a formula, f, check to see if f has already been identified.
    # If so, return the saved copy with f's identifier.
    # If not, save f as the representative copy ("reference formula") and assign it a new numeric identifier.

    # IMPORTANT: Assumes that all of f's sub-formulae have already been given numeric identifiers.
    def reference_formula(self, f):
        if f.get_id() is not None:
            return self.id_to_formula[f.get_id()]

        tuple_id = self.get_tuple_id(f)
        if tuple_id in self.tuple_id_to_numeric_id:
            result = self.id_to_formula[self.tuple_id_to_numeric_id[tuple_id]]
            f.set_id(result.get_id)
            return result

        f.set_id(self.next_numeric_id)
        self.tuple_id_to_numeric_id[tuple_id] = self.next_numeric_id
        self.id_to_formula[self.next_numeric_id] = f
        self.id_to_containing_ids[self.next_numeric_id] = set()
        t = f.get_type()
        if t != BF_POS_LIT and t != BF_NEG_LIT:
            for sub_f in f.get_contents():
                self.id_to_containing_ids[sub_f.get_id()].add(self.next_numeric_id)
        self.next_numeric_id += 1
        return f

    def get_tuple_id(self, f):
        t = f.get_type()
        if t == BF_POS_LIT or t == BF_NEG_LIT:
            var_list = f.get_contents()
            var = var_list[0]
            return (t, var)
        return (t, tuple(sorted([x.get_id() for x in f.get_contents()])))

    def get_formula_from_id(self, identifier):
        return self.id_to_formula[identifier]

    def gen_literal_formula(self, t, variable):
        if t != BF_POS_LIT and t != BF_NEG_LIT:
            raise ValueError("Error! type t not one of the literal types")

        return self.reference_formula(BooleanFormula(t, [variable], None))

    # Assumes that the sub_formulae have already been added to the bank.
    def gen_op_formula(self, operator, sub_formulae):
        if operator == BF_NOT:
            if len(sub_formulae) != 1:
                raise ValueError("Error! Cannot create NOT formula with %d sub_formulae" % len(sub_formulae))
            if sub_formulae[0].get_type() == BF_POS_LIT:
                return self.reference_formula(BooleanFormula(BF_NEG_LIT, sub_formulae[0].get_contents(), None))
            if sub_formulae[0].get_type() == BF_NEG_LIT:
                return self.reference_formula(BooleanFormula(BF_POS_LIT, sub_formulae[0].get_contents(), None))
            if sub_formulae[0].get_type() == BF_NOT:
                return self.reference_formula(sub_formulae[0].get_contents()[0])
        elif operator == BF_AND or operator == BF_OR:
            if len(sub_formulae) < 2:
                raise ValueError("Error! Cannot create an AND or and OR formula with fewer than 2 sub-formulae")
        else:
            raise ValueError("Error! operator is not one of the operator types")

        return self.reference_formula(BooleanFormula(operator, list(sub_formulae), None))

    def replace_all_occurrences_of_formula(self, orig, replacement):
        orig_id = orig.get_id()
        replacement_id = replacement.get_id()
        if orig_id is None:
            raise ValueError("Error! original formula does not have an id.")
        if replacement_id is None:
            raise ValueError("Error! replacement formula does not have an id.")

        # Update records for all containers of the original formula
        for container_id in self.id_to_containing_ids[orig_id]:
            container_f = self.id_to_formula[container_id]
            sub_fs = container_f.get_actual_contents()
            original_container_tuple_id = self.get_tuple_id(container_f)
            for i in range(0, len(sub_fs)):
                if sub_fs[i].get_id() == orig_id:
                    sub_fs[i] = self.reference_formula(replacement) # TODO: Can this just be `replacement`?`
                    break
            new_container_tuple_id = self.get_tuple_id(container_f)
            del self.tuple_id_to_numeric_id[original_container_tuple_id]
            self.tuple_id_to_numeric_id[new_container_tuple_id] = container_id

            # Also, add that the replacement formula is now contained by these.
            self.id_to_containing_ids[replacement_id].add(container_id)

        # Delete the original formula from the bank.
        orig_tuple_id = self.get_tuple_id(orig)
        if orig.get_type() != BF_POS_LIT and orig.get_type() != BF_NEG_LIT:
            for sub_f in orig.get_contents():
                sub_f_id = sub_f.get_id()
                self.id_to_containing_ids[sub_f_id].remove(orig_id)

        del self.tuple_id_to_numeric_id[orig_tuple_id]
        del self.id_to_containing_ids[orig_id]
        del self.id_to_formula[orig_id]

        # Handle double-negatives and negations of literals.
        if replacement.get_type() == BF_NOT:
            for container_id in list(self.id_to_containing_ids[replacement_id]): # Copied because the original might be modified by the loop.
                container_f = self.id_to_formula[container_id]
                if container_f.get_type() == BF_NOT:
                    self.replace_all_occurrences_of_formula(container_f, replacement.get_contents()[0])

        if replacement.get_type() == BF_POS_LIT or replacement.get_type() == BF_NEG_LIT:
            opposite_type = BF_POS_LIT
            if opposite_type == replacement.get_type():
                opposite_type = BF_NEG_LIT
            opposite_lit = BooleanFormula(opposite_type, replacement.get_contents(), None)

            for container_id in list(self.id_to_containing_ids[replacement_id]): # Copied because the original might be modified by the loop.
                container_f = self.id_to_formula[container_id]
                if container_f.get_type() == BF_NOT:
                    self.replace_all_occurrences_of_formula(container_f, self.reference_formula(opposite_lit))

    def gen_formula_from_string(self, s, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")"):
        return self.init_from_string_in_place(s, and_str=and_str, or_str=or_str, not_str = not_str, left_par_str=left_par_str, right_par_str=right_par_str)

    def clean_string_in_place(self, s, start_pos=None, end_pos=None, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")"):
        # Remove whitespace.
        first_clean = start_pos is None
        if first_clean:
            s2 = ""
            for c in s:
                if c != " ":
                    s2 += c
            s = s2
            start_pos = 0
            end_pos = len(s)

        # Remove extra parens at start and end if there are any extras.
        # (determined by lowest point reached before the end of the string and AFTER at least one left paren)
        first_climb_height = 0
        end_of_first_climb = start_pos
        idx = start_pos
        while idx < end_pos and s.startswith(left_par_str, idx):
            idx += len(left_par_str)
            first_climb_height += 1
        end_of_first_climb = idx

        last_descent_height = 0
        start_of_last_descent = start_pos
        idx = end_pos
        while idx > start_pos and s.startswith(right_par_str, idx - len(right_par_str)):
            idx -= len(right_par_str)
            last_descent_height += 1
        start_of_last_descent = idx

        parens_to_remove = 0
        if end_of_first_climb + 1 == start_of_last_descent:
            if first_climb_height != last_descent_height:
                print("JUSTUS DOES NOT KNOW WHAT HE IS DOING! ABORT! :(")
                exit(1)
            parens_to_remove = first_climb_height
        elif first_climb_height > 0:
            idx = end_of_first_climb
            parens_to_remove = first_climb_height
            height = first_climb_height
            while idx < start_of_last_descent:
                if s.startswith(left_par_str, idx):
                    idx += len(left_par_str)
                    height += 1
                elif s.startswith(right_par_str, idx):
                    idx += len(right_par_str)
                    height -= 1
                    if height < parens_to_remove:
                        parens_to_remove = height
                    if height < 0:
                        raise ValueError("ERROR: malformed parentheses (or code??)")
                else:
                    idx += 1
            if height != last_descent_height:
                raise ValueError("ERROR: malformed parentheses")
        new_start = start_pos + parens_to_remove * len(left_par_str)
        new_end = end_pos - parens_to_remove * len(right_par_str)
        if first_clean: # If this is the very first clean (whitespace was removed).
            s = s[new_start:new_end]
            new_start = 0
            new_end = len(s)
        return s, new_start, new_end

    def init_from_string_in_place(self, s, start_pos=None, end_pos=None, and_str="&&", or_str="||", not_str="~",\
            left_par_str="(", right_par_str=")"):

        s, start_pos, end_pos = self.clean_string_in_place(s, start_pos, end_pos, and_str=and_str, or_str=or_str, not_str=not_str,\
            left_par_str=left_par_str, right_par_str=right_par_str)

        type_val = 0
        sub_formulae_vals = []

        # Partition
        segments = []
        height = 0
        main_op = None
        starts_with_not = False
        idx = start_pos
        next_segment_start = start_pos
        while idx < end_pos:
            if s.startswith(and_str, idx):
                idx += len(and_str)
                if height == 0:
                    if main_op is None or main_op == BF_AND:
                        main_op = BF_AND
                        seg_end_pos = idx - len(and_str)
                        segments.append((next_segment_start, seg_end_pos))
                        next_segment_start = idx
                    else: # main_op is BF_OR
                        idx = end_pos # i.e. done

            elif s.startswith(or_str, idx):
                idx += len(or_str)
                if height == 0:
                    if main_op is None or main_op == BF_OR:
                        main_op = BF_OR
                        seg_end_pos = idx - len(or_str)
                        segments.append((next_segment_start,seg_end_pos))
                        next_segment_start = idx
                    else: # main op is BF_AND
                        idx = end_pos # i.e. done

            elif s.startswith(not_str, idx):
                if idx == start_pos:
                    starts_with_not = True
                idx += len(not_str)

            elif s.startswith(left_par_str, idx):
                idx += len(left_par_str)
                height += 1

            elif s.startswith(right_par_str, idx):
                idx += len(right_par_str)
                height -= 1

            else: # presumed to be part of a literal
                idx += 1

        if next_segment_start == start_pos:
            if starts_with_not:
                new_start_pos = start_pos + len(not_str)
                negated_formula = self.init_from_string_in_place(s, start_pos=new_start_pos, end_pos=end_pos, \
                    and_str=and_str, or_str=or_str, not_str=not_str, left_par_str=left_par_str, right_par_str=right_par_str)
                type_val = BF_NOT
                sub_formulae_vals = [negated_formula]
            else:
                literal = s[start_pos:end_pos]
                type_val = BF_POS_LIT
                sub_formulae_vals = [literal]
        else:
            segments.append((next_segment_start,end_pos))
            # print("It's an oppy op!")
            # print(segments)
            type_val = main_op
            for segment in segments:
                sub_formulae_vals.append(\
                    self.init_from_string_in_place(s, start_pos=segment[0], end_pos=segment[1], \
                        and_str=and_str, or_str=or_str, not_str=not_str, left_par_str=left_par_str, right_par_str=right_par_str))

        print(type_val)
        print(sub_formulae_vals)
        return self.reference_formula(BooleanFormula(type_val, sub_formulae_vals, None))

"""
BFB = BooleanFormulaeBank()
f1 = BFB.gen_literal_formula(BF_POS_LIT, "x1")
f2 = BFB.gen_literal_formula(BF_NEG_LIT, "x1")
f3 = BFB.gen_literal_formula(BF_NEG_LIT, "x2")
f4 = BFB.gen_op_formula(BF_AND, [f1, f2])
f5 = BFB.gen_op_formula(BF_NOT, [f1])
f6 = BFB.gen_op_formula(BF_NOT, [f4])
f7 = BFB.gen_op_formula(BF_NOT, [f6])
f8 = BFB.gen_op_formula(BF_OR, [f3, f6])
print(f5.get_type() == BF_NEG_LIT)
print(f6.get_type() == BF_NOT)
print(f7.get_type() == BF_AND)
print(f7 == f4)
print(f8.to_string(with_spaces=True))
BFB.replace_all_occurrences_of_formula(f4, f3)
print("----------------------------")
for i, f in BFB.id_to_formula.items():
    print("")
    print(f.get_type())
    print(f.get_contents())

f9 = BFB.gen_formula_from_string("(a && b) && (~a || ~(c || bug))")
print(f9.to_string(with_spaces=True))
print(BFB.gen_formula_from_string("~(~a)").to_string()) # TODO: Make this return "a"
"""
