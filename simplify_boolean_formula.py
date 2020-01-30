from boolean_formulae import *
import subprocess
import sys

# Check out https://users.ece.utexas.edu/~patt/06s.382N/tutorial/espresso_manual.html
# Also: http://www.ecs.umass.edu/ece/labs/vlsicad/ece667/links/espresso.html

def simplify_boolean_formula(bf, filename="espresso_binaries/formula_to_simplify", bfb=None):
    var_ids = {}
    _, assignments = get_satisfying_assignments(bf, var_ids)
    
    create_espresso_input_file(assignments, var_ids, filename)

    proc = subprocess.Popen(["./espresso_binaries/espresso", "-o", "eqntott", filename],
                          stdout=subprocess.PIPE)
    output, error = proc.communicate()
    if sys.version_info[0] == 3:
        formula_string = output.decode()
    else:
        formula_string = output
    formula_string = formula_string.replace("\n", "")
    formula_string = formula_string.replace(";", "")
    formula_string = formula_string[9:]

    if bfb is None:
        bfb = BooleanFormulaeBank()
    simplified = bfb.gen_formula_from_string(formula_string, and_str="&", or_str="|", not_str="!")
    return simplified

def advanced_simplify_boolean_formula(bf, filename="espresso_binaries/formula_to_simplify", bfb=None, depth=0):
    if bfb is None:
        bfb = BooleanFormulaeBank()
        bf = bfb.gen_formula_from_string(bf.to_string())

    if bf.get_type() == BF_POS_LIT or bf.get_type() == BF_NEG_LIT:
        bf = bfb.reference_formula(bf)
        return bf

    the_label = str(bfb.get_tuple_id(bf)) # Make sure to tag this formula uniquely so we can access it later.
    bf = bfb.reference_formula(bf, external_label=the_label)

    completed = set()
    anything_unexpected = False
    while len(completed) != len(bf.get_contents()):
        contents = bf.get_contents()
        for sub_f in contents:
            if sub_f.get_id() not in completed:
                if anything_unexpected:
                    print("A")
                simplified = advanced_simplify_boolean_formula(sub_f, filename, bfb, depth+1)
                if anything_unexpected:
                    print("B")
                if sub_f.get_id() in bfb.id_to_formula:
                    bfb.replace_all_occurrences_of_formula(sub_f, simplified)
                    bf = bfb.get_formula_from_external_label(the_label)
                else:
                    print("This is unexpected.")
                    anything_unexpected = True
                completed.add(simplified.get_id())
                if anything_unexpected:
                    print(completed)
                break
            if anything_unexpected:
                print("Holler")
        if anything_unexpected:
            print("Dollar")
    if anything_unexpected:
        print("Loop done")

    bf = bfb.get_formula_from_external_label(the_label)
    var_ids = {}

    if anything_unexpected:
        print("Getting satisfying assignments")
    _, assignments = get_satisfying_assignments(bf, var_ids)
    
    if anything_unexpected:
        print("Creating espresso file")
    create_espresso_input_file(assignments, var_ids, filename)

    proc = subprocess.Popen(["./espresso_binaries/espresso", "-o", "eqntott", filename],
                          stdout=subprocess.PIPE)
    output, error = proc.communicate()
    if sys.version_info[0] == 3:
        formula_string = output.decode()
    else:
        formula_string = output
    formula_string = formula_string.replace("\n", "")
    formula_string = formula_string.replace(";", "")
    formula_string = formula_string[9:]
    simplified = bfb.gen_formula_from_string(formula_string, and_str="&", or_str="|", not_str="!")

    print("Completed at depth: %s%s" % ("".join(["   " for i in range(0, 10 - depth)]), depth))
    return simplified

def create_espresso_input_file(satisfying_assignments, var_ids, filename):
    id_to_var = {i: v for v, i in var_ids.items()}

    f = open(filename, "w")
    f.write(".i %d\n" % len(var_ids)) # Number of inputs
    f.write(".o 1\n") # 1 output
    var_names_in_order = [" %s" % x[1] for x in sorted([(i, var) for i, var in id_to_var.items()])]
    f.write(".ilb %s\n" % "".join(var_names_in_order))
    f.write(".ob OUTPUT\n") # Name of output.

    for assignment in satisfying_assignments:
        assignment_array = ["-" for var in range(0, len(var_ids))]
        for (var_id, true_or_false) in assignment:
            if true_or_false:
                assignment_array[var_id] = "1"
            else:
                assignment_array[var_id] = "0"
        assignment_array.append(" 1\n")
        f.write("".join(assignment_array))

    f.write(".e\n")
    f.close()

def get_satisfying_assignments(bf, var_ids, next_var_id=0, depth=0):
    print("Sat assign called")
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
        next_var_id, sub_assignments = get_satisfying_assignments(bf.get_contents()[0], var_ids, next_var_id, depth+1)
        # after applying the negation it's in the form:
        # (~x1 or ~x2 or ~~x3) and (~x1 or ~x5) and ...

        # A satisfying assignment is thus a negation of a literal from one of each of the sub_assignments.
        limits = [len(sa) - 1 for sa in sub_assignments]
        counters = [0 for sa in sub_assignments]
        counters[-1] = -1
        print(limits)
        print(depth)
        while increment_counters_with_limits(counters, limits):
            assignments.append(list(set([(sub_assignments[i][counters[i]][0], not sub_assignments[i][counters[i]][1]) for i in range(0, len(counters))])))
    elif bf.get_type() == BF_OR:
        for sub_f in bf.get_contents():
            next_var_id, sub_assignments = get_satisfying_assignments(sub_f, var_ids, next_var_id, depth+1)
            assignments += sub_assignments
    else: # BF_AND
        # Here we have an and-of-or-of-ands situation.
        sub_results = []
        for sub_f in bf.get_contents():
            next_var_id, sub_assignments = get_satisfying_assignments(sub_f, var_ids, next_var_id, depth+1)
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
    print("Found sat assign at depth: %s%s" % ("".join(["   " for i in range(0, 10 - depth)]), depth))
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
#var_ids = {}
#_, assignments = get_satisfying_assignments(d, var_ids)
#reverse_var_ids = {i: v for v, i in var_ids.items()}
#for assignment in assignments:
#    print([(reverse_var_ids[x[0]], x[1]) for x in assignment])

simplify_boolean_formula(d)

f = open("./saved_5_nn_formulae.txt")
first_formula = f.readline()
if first_formula[-1] == "\n":
    first_formula = first_formula[0:-1]
orig = BFB.gen_formula_from_string(first_formula)
print("The original formula had %d characters" % len(orig.to_string(with_spaces=False)))
simplified = advanced_simplify_boolean_formula(orig, bfb=BFB)
print("The simplified formula had %d characters" % len(simplified.to_string(with_spaces=False)))
