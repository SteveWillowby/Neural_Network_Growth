# BooleanFormula interface:
#
#   init_from_string(s, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")")
#   
#   to_string(and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")")
#
#
#   get_variables()
#       returns a set of all the variable names. O(formula size)
#
#   get_variables_risky()
#
#   get_literals()
#       returns a set of all the variable names, but add negations for negated literals. O(formula size)
#
#   deep_copy()
#       returns a deep copy of the formula
#
#   super_shallow_copy()
#       use at your own risk
#
#   replace_variable(var, formula)
#       replaces every occurrence of var with formula
#
#   shallow_replace_variable(var, formula)
#       use at your own risk (points to formula)

class BooleanFormula:

    def __init__(self):
        self.f = []
        self.OR = "or"
        self.AND = "and"
        self.NOT = "not"
        self.VARIABLE = "var"
        self.var_ptr_sets = {}
        self.parent = None
        self.id = ""

    # Reads the string from left? to right?

    # So "A && B || C" means "A && (B || C)"
    #    "A && B || C && D" means "A && (B || (C && D))"
    # Note: A && B && (C || D) <--> A && (B && (C || D))
    def init_from_string(self, s, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")", parent=None, shallow=False):
        the_ids = None
        if shallow:
            the_ids = [0, {}]
        self.init_from_string_in_place(s, and_str=and_str, or_str=or_str, not_str=not_str,\
            left_par_str=left_par_str, right_par_str=right_par_str, the_ids=the_ids)
        return

    def add_var_ptr_sets(self, other, del_other_ptrs_on_completion=False):
        for var, ptrs in other.var_ptr_sets.items():
            if var in self.var_ptr_sets:
                self.var_ptr_sets[var] |= ptrs
            else:
                self.var_ptr_sets[var] = ptrs
        if del_other_ptrs_on_completion:
            other.var_ptr_sets = {}

    def to_string(self, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")"):
        if self.f[0] == self.VARIABLE:
            return self.f[1]
        elif self.f[0] == self.NOT:
            return "%s%s" % (not_str, self.f[1].to_string())
        else:
            op_str = or_str
            if self.f[0] == self.AND:
                op_str = and_str
            res = left_par_str
            idx = 1
            while idx < len(self.f):
                res += self.f[idx].to_string()
                if idx < len(self.f) - 1:
                    res += " %s " % op_str
                idx += 1
            res += right_par_str
            return res


    def get_variables(self):
        if self.f[0] == self.VARIABLE:
            return set([self.f[1]])
        result = set()
        for i in range(1, len(self.f)):
            partial = self.f[i].get_variables()
            result |= partial
        return result

    def get_variables_risky(self):
        return set([var for var, ptrs in self.var_ptr_sets.items()])

    def get_literals(self):
        if self.f[0] == self.VARIABLE:
            return set([self.f[1]])
        if self.f[0] == self.NOT and self.f[1].f[0] == self.VARIABLE:
            return set(["~%s" % self.f[1].f[1]])
        result = set()
        for i in range(1, len(self.f)):
            partial = self.f[i].get_variables()
            result |= partial
        return result

    def deep_copy(self):
        print("Danger. Deep copying a boolean formula destroys the var_ptr_sets' correctness.")
        dc = BooleanFormula()
        if self.f[0] == self.VARIABLE:
            dc.f = [str(self.VARIABLE), str(self.f[1])]
        else:
            dc.f = [str(self.f[0])]
            for i in range(1, len(self.f)):
                dc.f.append(self.f[i].deep_copy())
        return dc

    def replace_variable(self, var, formula):
        print("THIS FUNCTION SHOULD NOT BE CALLED! (replace_variable())")
        exit(1)
        if self.f[0] == self.VARIABLE:
            if self.f[1] == var:
                self.f = [str(formula.f[0])]
                if formula.f[0] == formula.VARIABLE:
                    self.f.append(str(formula.f[1]))
                else:
                    for i in range(1, len(formula.f)):
                        self.f.append(formula.f[i].deep_copy())
        else:
            for i in range(1, len(self.f)):
                self.f[i].replace_variable(var, formula)

    #def super_shallow_copy(self):
    #    sc = BooleanFormula()
    #    sc.f = self.f
    #    sc.var_ptr_sets = self.var_ptr_sets
    #    return sc

    def shallow_replace_variable(self, var, formula):
        if self.f[0] == self.VARIABLE:
            if self.f[1] == var:
                self.f = formula.f
                del self.var_ptr_sets[var]
                self.add_var_ptr_sets(formula)
        else:
            var_locations = self.var_ptr_sets[var] 
            for (ptr, idx) in var_locations:
                ptr.f[idx] = formula
            del self.var_ptr_sets[var]
            self.add_var_ptr_sets(formula)

    # Arranges formula in a kind of lexicographic ordering.
    def sort(self):
        print("Danger. Sorting a boolean formula destroys the var_ptr_sets' correctness.")
        if self.f[0] == self.VARIABLE:
            return
        if self.f[0] == self.NOT:
            self.f[1].sort()
        else:
            string_idx_pairs = []
            for i in range(1, len(self.f)):
                self.f[i].sort()
                string_idx_pairs.append((self.f[i].to_string(), i))
            string_idx_pairs.sort()
            new_f = [self.f[0]]
            for i in range(0, len(self.f) - 1):
                new_f.append(self.f[string_idx_pairs[i][1]])
            self.f = new_f

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
                        print("ERROR: malformed parentheses (or code??)")
                        exit(1)
                else:
                    idx += 1
            if height != last_descent_height:
                print("ERROR: malformed parentheses")
                exit(1)
        new_start = start_pos + parens_to_remove * len(left_par_str)
        new_end = end_pos - parens_to_remove * len(right_par_str)
        if first_clean: # If this is the very first clean (whitespace was removed).
            s = s[new_start:new_end]
            new_start = 0
            new_end = len(s)
        return s, new_start, new_end

    def init_from_string_in_place(self, s, start_pos=None, end_pos=None, and_str="&&", or_str="||", not_str="~",\
            left_par_str="(", right_par_str=")", parent=None, the_ids=None):
        self.parent = parent
        s, start_pos, end_pos = self.clean_string_in_place(s, start_pos, end_pos, and_str=and_str, or_str=or_str, not_str=not_str,\
            left_par_str=left_par_str, right_par_str=right_par_str)

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
                    if main_op is None or main_op == self.AND:
                        main_op = self.AND
                        seg_end_pos = idx - len(and_str)
                        segments.append((next_segment_start, seg_end_pos))
                        next_segment_start = idx
                    else: # main_op is self.OR
                        idx = end_pos # i.e. done

            elif s.startswith(or_str, idx):
                idx += len(or_str)
                if height == 0:
                    if main_op is None or main_op == self.OR:
                        main_op = self.OR
                        seg_end_pos = idx - len(or_str)
                        segments.append((next_segment_start,seg_end_pos))
                        next_segment_start = idx
                    else: # main op is self.AND
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
                negated_formula = BooleanFormula()
                new_start_pos = start_pos + len(not_str)
                negated_formula.init_from_string_in_place(s, start_pos=new_start_pos, end_pos=end_pos, parent=self,\
                    and_str=and_str, or_str=or_str, not_str=not_str, left_par_str=left_par_str, right_par_str=right_par_str, the_ids=the_ids)
                if negated_formula.f[0] == self.NOT: # It's a double-negative!
                    self.f = negated_formula.f[1].f
                    self.id = negated_formula.f[1].id
                    self.var_ptr_sets = negated_formula.f[1].var_ptr_sets
                else:
                    if the_ids is not None:
                        self.id = ''.join([self.NOT, ":", str(the_ids[1][negated_formula.id][0])])
                        self.f = [self.NOT, the_ids[1][negated_formula.id][1]]
                    else:
                        self.f = [self.NOT, negated_formula]
                    self.add_var_ptr_sets(self.f[1])
            else:
                literal = s[start_pos:end_pos]
                # print("It's a literal! called: %s" % literal)
                self.f = [self.VARIABLE, literal]
                if self.parent is not None:
                    self.var_ptr_sets[literal] = set([(self.parent, len(self.parent.f) - 1)])

                if the_ids is not None:
                    self.id = ''.join([self.VARIABLE, ":", literal])
        else:
            segments.append((next_segment_start,end_pos))
            # print("It's an oppy op!")
            # print(segments)
            self.f = [main_op]
            for segment in segments:
                self.f.append(BooleanFormula())
                self.f[-1].init_from_string_in_place(s, start_pos=segment[0], end_pos=segment[1], parent=self,\
                    and_str=and_str, or_str=or_str, not_str=not_str, left_par_str=left_par_str, right_par_str=right_par_str, the_ids=the_ids)
                self.add_var_ptr_sets(self.f[-1])
            if the_ids is not None:
                sub_ids = []
                for sub_idx in range(1, len(self.f)):
                    sub_f = self.f[sub_idx]
                    self.f[sub_idx] = the_ids[1][sub_f.id][1]
                    sub_ids.append(the_ids[1][sub_f.id][0])
                self.id = ''.join([self.VARIABLE, ":", str(sorted(sub_ids))])

        if the_ids is not None:
            if self.id not in the_ids[1]:
                the_ids[1][self.id] = (the_ids[0], self)
                the_ids[0] += 1

        """
        # The rest of the code is legacy - left here in case there's a bug with the in place version.

        self.parent = parent
        s = self.clean_string(s, and_str=and_str, or_str=or_str, not_str=not_str, left_par_str=left_par_str, right_par_str=right_par_str)

        if start_pos is None:
            start_pos = 0
        if end_pos is None:
            end_pos = len(s)

        # Partition
        segments = []
        height = 0
        main_op = None
        starts_with_not = False
        idx = 0
        next_segment_start = 0
        while idx < len(s):
            if s.startswith(and_str, idx):
                idx += len(and_str)
                if height == 0:
                    if main_op is None or main_op == self.AND:
                        main_op = self.AND
                        end_pos = idx - len(and_str)
                        segments.append(s[next_segment_start:end_pos])
                        next_segment_start = idx
                    else: # main_op is self.OR
                        idx = len(s) # i.e. done

            elif s.startswith(or_str, idx):
                idx += len(or_str)
                if height == 0:
                    if main_op is None or main_op == self.OR:
                        main_op = self.OR
                        end_pos = idx - len(or_str)
                        segments.append(s[next_segment_start:end_pos])
                        next_segment_start = idx
                    else: # main op is self.AND
                        idx = len(s) # i.e. done

            elif s.startswith(not_str, idx):
                if idx == 0:
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

        if next_segment_start == 0:
            if starts_with_not:
                negated = s[len(not_str):len(s)]
                # print("It's a negation! of: %s" % negated)
                negated_formula = BooleanFormula()
                negated_formula.init_from_string(negated, parent=self)
                self.f = [self.NOT, negated_formula]
                self.add_var_ptr_sets(self.f[1])
            else:
                literal = s
                # print("It's a literal! called: %s" % literal)
                self.f = [self.VARIABLE, literal]
                if self.parent is not None:
                    self.var_ptr_sets[literal] = set([(self.parent, len(self.parent.f) - 1)])
        else:
            segments.append(s[next_segment_start:len(s)])
            # print("It's an oppy op!")
            # print(segments)
            self.f = [main_op]
            for segment in segments:
                self.f.append(BooleanFormula())
                self.f[-1].init_from_string(segment, parent=self)
                self.add_var_ptr_sets(self.f[-1])

    def clean_string(self, s, and_str="&&", or_str="||", not_str="~", left_par_str="(", right_par_str=")"):
        # Remove whitespace.
        s2 = ""
        for c in s:
            if c != " ":
                s2 += c
        s = s2

        # Remove extra parens at start and end if there are any extras.
        # (determined by lowest point reached before the end of the string and AFTER at least one left paren)
        first_climb_height = 0
        end_of_first_climb = 0
        idx = 0
        while idx < len(s) and s.startswith(left_par_str, idx):
            idx += len(left_par_str)
            first_climb_height += 1
        end_of_first_climb = idx

        last_descent_height = 0
        start_of_last_descent = 0
        idx = len(s)
        while idx > 0 and s.startswith(right_par_str, idx - len(right_par_str)):
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
                        print("ERROR: malformed parentheses (or code??)")
                        exit(1)
                else:
                    idx += 1
            if height != last_descent_height:
                print("ERROR: malformed parentheses")
                exit(1)
        new_start = parens_to_remove * len(left_par_str)
        new_end = len(s) - parens_to_remove * len(right_par_str)
        s = s[new_start:new_end]
        return s
        """
"""
B1 = BooleanFormula()
B2 = BooleanFormula()
B1.init_from_string_in_place("( (~(xi ) && x_k && (~xj) || ( xi))   )   && ~T")
print(B1.to_string())
B2.init_from_string(B1.to_string())
print(B1.to_string())
print(B1.get_variables())
B2 = BooleanFormula()
B2.init_from_string("a || b")
B1.shallow_replace_variable("xi", B2)
print(B1.to_string())
"""
