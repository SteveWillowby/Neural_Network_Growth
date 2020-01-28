

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

    def gen_formula_from_string(self, s):
        pass
"""
BFB = BooleanFormulaeBank()
f1 = BFB.gen_literal_formula(BF_POS_LIT, "x1")
f2 = BFB.gen_literal_formula(BF_NEG_LIT, "x1")
f3 = BFB.gen_literal_formula(BF_NEG_LIT, "x2")
f4 = BFB.gen_op_formula(BF_AND, [f1, f2])
f5 = BFB.gen_op_formula(BF_NOT, [f1])
f6 = BFB.gen_op_formula(BF_NOT, [f4])
f7 = BFB.gen_op_formula(BF_NOT, [f6])
print(f5.get_type() == BF_NEG_LIT)
print(f6.get_type() == BF_NOT)
print(f7.get_type() == BF_AND)
print(f7 == f4)
BFB.replace_all_occurrences_of_formula(f4, f3)
print("----------------------------")
for i, f in BFB.id_to_formula.items():
    print("")
    print(f.get_type())
    print(f.get_contents())
"""
