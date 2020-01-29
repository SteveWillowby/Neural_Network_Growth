from boolean_formulae import *

# Check out https://users.ece.utexas.edu/~patt/06s.382N/tutorial/espresso_manual.html
# Also: http://www.ecs.umass.edu/ece/labs/vlsicad/ece667/links/espresso.html

def get_satisfying_assignments(bf, var_ids, next_var_id=1):
    assignments = []
    if bf.get_type() == BF_POS_LIT or bf.get_type() == BF_NEG_LIT:
        var = bf.get_contents()[0]
        if var in var_ids:
            var_id = var_ids[var]
        else:
            var_id = next_var_id
            var_ids[var] = next_var_id
            next_var_id += 1
        truth_assignment = bf.get_type() == BF_POS_LIT
        assignments.append([(var_id, truth_assignment)])
    elif bf.get_type() == BF_NOT:
        # Assignments from sub-calls are essentially DNFs.
        next_var_id, sub_assignments = get_satisfying_assignments(bf.get_contents()[0], var_ids, next_var_id)
        # after applying the negation it's in the form:
        # (~x1 or ~x2 or ~~x3) and (~x1 or ~x5) and ...

        # A satisfying assignment is thus a negation of a literal from one of each of the sub_assignments.
        limits = [len(sa) - 1 for sa in sub_assignments]
        counters = [0 for sa in sub_assignments]
        counters[-1] = -1
        while increment_counters_with_limits(counters, limits):
            print(counters)
            assignments.append(list(set([(sub_assignments[i][counters[i]][0], not sub_assignments[i][counters[i]][1]) for i in range(0, len(counters))])))
    elif bf.get_type() == BF_OR:
        for sub_f in bf.get_contents():
            next_var_id, sub_assignments = get_satisfying_assignments(sub_f, var_ids, next_var_id)
            assignments += sub_assignments
    else: # BF_AND
        # Here we have an and-of-or-of-ands situation.
        sub_results = []
        for sub_f in bf.get_contents():
            next_var_id, sub_assignments = get_satisfying_assignments(sub_f, var_ids, next_var_id)
            sub_results.append(sub_assignments)
        limits = [len(sr) - 1 for sr in sub_results]
        counters = [0 for sr in sub_results]
        counters[-1] = -1
        while increment_counters_with_limits(counters, limits):
            assignments.append(list(set(list_concat([sub_results[i][counters[i]] for i in range(0, len(counters))]))))

    assignment_hashes = set()
    final_assignments = []
    for assignment in assignments:
        if len(set([x[0] for x in assignment])) < len(assignment):
            continue
        hashable = tuple(sorted(assignment))
        if hashable in assignment_hashes:
            continue
        assignment_hashes.add(hashable)
        final_assignments.append(assignment)
    return next_var_id, final_assignments

# Returns true if increment successful. False if impossible.
def increment_counters_with_limits(counters, limits):
    i = len(counters) - 1
    while counters[i] == limits[i]:
        i -= 1
        if i < 0:
            return False
    counters[i] += 1
    for j in range(i + 1, len(counters)):
        counters[j] = 0
    return True

def list_concat(list_of_lists):
    res = list(list_of_lists[0])
    for i in range(1, len(list_of_lists)):
        res += list_of_lists[i]
    return res

BFB = BooleanFormulaeBank()
x1 = BFB.gen_literal_formula(BF_POS_LIT, "x1")
n_x1 = BFB.gen_literal_formula(BF_NEG_LIT, "x1")
x2 = BFB.gen_literal_formula(BF_POS_LIT, "x2")
x3 = BFB.gen_literal_formula(BF_POS_LIT, "x3")

a = BFB.gen_op_formula(BF_AND, [x1, x2])
b = BFB.gen_op_formula(BF_OR, [n_x1, x2])
c = BFB.gen_op_formula(BF_OR, [x3, x1])
d = BFB.gen_op_formula(BF_AND, [a, b, c])
print(d.to_string(with_spaces=True))
var_ids = {}
_, assignments = get_satisfying_assignments(d, var_ids)
reverse_var_ids = {i: v for v, i in var_ids.items()}
for assignment in assignments:
    print([(reverse_var_ids[x[0]], x[1]) for x in assignment])
