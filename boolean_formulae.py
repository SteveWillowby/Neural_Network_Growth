

class BooleanFormula:

    def __init__(self, formula_bank):
        self.op = None
        self.sub_formulae = []
        self.formula_bank = formula_bank
        self.id = None

    def fill_out_from_string(self, s):
        pass

    def fill_out_as_literal(self, variable, true_or_false):
        pass

    def fill_out_as_op(self, operator, sub_formulae):
        pass

    def fill_out_as_formula_with_var_replaced(self, orig, var, replacement):
        pass

    def get_id(self):
        return self.id

    def get_op(self):
        return self.op

    def get_sub_formulae(self):
        return list(self.sub_formulae) # TODO: Consider whether removing the copy for efficiency is worthwhile

class BooleanSubFormulaeBank:

    def __init__(self):
        self.next_numeric_id = 1
        self.literal_to_id = {}
        self.id_to_formula = {}

    def reference_formula(self, f):
        if f.get_id() is not None:
            return self.id_to_formula[f.get_id()]
        f.id_tuple = (f.op, sorted())

    def get_formula_from_id(self, identifier):
        return self.id_to_formula[identifier]
