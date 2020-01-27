

BF_POS_LIT = 1
BF_NEG_LIT = 2
BF_AND = 3
BF_OR = 4
BF_NOT = 5

class BooleanFormula:

    def __init__(self, formulae_bank):
        self.op = None
        self.sub_formulae = []
        self.formulae_bank = formulae_bank
        self.id = None

    def fill_out_from_string(self, s):
        pass

    def fill_out_as_literal(self, variable, true_or_false):
        pass

    # TODO: Move the fill_out_... functionality into the BooleanFormulaeBank class and leave this class as minimal.

    # Assumes that the sub_formulae have already been added to the bank.
    def fill_out_as_op(self, operator, sub_formulae):
        self.op = operator
        self.sub_formulae = list(sub_formulae)
        ref = self.formulae_bank.reference_formula(self)
        if ref != self:
            print("Eh Wat! Check out fill_out_as_op.")
        return ref

    def fill_out_as_formula_with_var_replaced(self, orig, var, replacement):
        if self.op == BF_POS_LIT:
            if self.sub_formulae[0] == var:
                self.__dict__ = replacement.__dict__
            return self.formulae_bank.reference_formula(self)
        elif self.op == BF_NEG_LIT:
            if self.sub_formulae[0] == var:
                self.op = BG_NOT
                self.sub_formulae = [replacement]
            return self.formulae_bank.reference_formula(self)
        else:
            

    def set_id(self, identifier):
        self.id = identifier

    def get_id(self):
        return self.id

    def get_op(self):
        return self.op

    def get_sub_formulae(self):
        return list(self.sub_formulae) # TODO: Consider whether removing the copy for the sake of efficiency is worthwhile

class BooleanFormulaeBank:

    def __init__(self):
        self.next_numeric_id = 1
        self.id_tuple_to_numeric_id = {}
        self.numeric_id_to_formula = {}


    # Given a formula, f, check to see if f has already been identified.
    # If so, return the saved copy with f's identifier.
    # If not, save f as the representative copy ("reference formula") and assign it a new numeric identifier.

    # IMPORTANT: Assumes that all of f's sub-formulae have already been given numeric identifiers.
    def reference_formula(self, f):
        if f.get_id() is not None:
            return self.numeric_id_to_formula[f.get_id()]
        op = f.get_op()
        if op == BF_POS_LIT or op == BF_NEG_LIT:
            var_list = f.get_sub_formulae()
            var = var_list[0]
            id_tuple = (op, var)
        else:
            id_tuple = (op, tuple(sorted([x.get_id() for x in f.get_sub_formulae()])))

        if id_tuple in self.id_tuple_to_numeric_id:
            result = self.numeric_id_to_formula[self.id_tuple_to_numeric_id[id_tuple]]
            f.set_id(result.get_id)
            return result

        f.set_id(self.next_numeric_id)
        self.id_tuple_to_formula = self.next_numeric_id
        self.numeric_id_to_formula[self.next_numeric_id] = f
        self.next_numeric_id += 1
        return f

    def get_formula_from_id(self, identifier):
        return self.numeric_id_to_formula[identifier]
