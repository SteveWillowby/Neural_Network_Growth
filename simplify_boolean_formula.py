from boolean_formulae import *
import subprocess
import sys
import time

# Check out https://users.ece.utexas.edu/~patt/06s.382N/tutorial/espresso_manual.html
# Also: http://www.ecs.umass.edu/ece/labs/vlsicad/ece667/links/espresso.html

def simplify_boolean_formula(bf, filename="espresso_binaries/formula_to_simplify", bfb=None):
    if bfb is None:
        bfb = BooleanFormulaeBank()
        bf = bfb.gen_formula_from_string(bf.to_string())

    our_var_ids = {}
    bf = ands_flushed_out(bf, bfb)
    simplified, _ = advanced_simplify_boolean_formula(bf, filename=filename, bfb=bfb, var_ids=our_var_ids)
    return simplified

def ands_flushed_out(bf, bfb):
    if bf.get_type() == BF_POS_LIT or bf.get_type() == BF_NEG_LIT:
        return bf
    contents = []
    if bf.get_type() == BF_AND:
        # (A and B and C) <--> not (not A or not B or not C)
        for sub_f in bf.get_contents():
            flushed_out_sub = ands_flushed_out(bfb.gen_op_formula(BF_NOT, [sub_f]), bfb)
            contents.append(flushed_out_sub)
        the_or = bfb.gen_op_formula(BF_OR, contents)
        return bfb.gen_op_formula(BF_NOT, [the_or])

    for sub_f in bf.get_contents():
        flushed_out_sub = ands_flushed_out(sub_f, bfb)
        contents.append(flushed_out_sub)
    return bfb.gen_op_formula(bf.get_type(), contents)

def advanced_simplify_boolean_formula(bf, filename="espresso_binaries/formula_to_simplify", bfb=None, assignments_bank={}, var_ids={}, next_var_id=0, depth=0):
    start_t = time.time()
    if bfb is None:
        bfb = BooleanFormulaeBank()
        bf = bfb.gen_formula_from_string(bf.to_string())

    if bf.get_id() in assignments_bank: # If this formula has already been simplified.
        print("Already done @dpth: %s%s  (%d)" % ("".join(["   " for i in range(0, 15 - depth)]), depth, time.time() - start_t))
        return bf, next_var_id

    if bf.get_type() == BF_POS_LIT or bf.get_type() == BF_NEG_LIT:
        bf = bfb.reference_formula(bf)
        var_name = bf.get_contents()[0]
        if var_name not in var_ids:
            var_ids[var_name] = next_var_id
            next_var_id += 1
        assignments_bank[bf.get_id()] = [[(var_ids[var_name], bf.get_type() == BF_POS_LIT)]]
        print("Literal   at depth: %s%s  (%d)" % ("".join(["   " for i in range(0, 15 - depth)]), depth, time.time() - start_t))
        return bf, next_var_id

    the_label = str(bfb.get_tuple_id(bf)) # Make sure to tag this formula uniquely so we can access it later.
    bf = bfb.reference_formula(bf, external_label=the_label)

    if bf.get_type() == BF_NOT:
        sub_f = bf.get_contents()[0]
        sub_simplified, next_var_id = advanced_simplify_boolean_formula(sub_f, filename, bfb, assignments_bank, var_ids, next_var_id, depth+1)
        if sub_f.get_id() in bfb.id_to_formula:
            # bfb.replace_all_occurrences_of_formula(sub_f, sub_simplified)
            bf = bfb.get_formula_from_external_label(the_label)
        else:
            print("This is unexpected.")
        sub_simplified_id = sub_simplified.get_id()
        # Get the minimized assignments for the negation of the sub-formula.
        assignments = assignments_from_assignments(assignments_bank[sub_simplified_id], var_ids, filename, negated=True)
        # Get the formula for these new negated assignments.
        simplified = formula_from_assignments(assignments, var_ids, filename, bfb, negated=False)
        assignments_bank[simplified.get_id()] = assignments
        assignments_bank[sub_f.get_id()] = assignments
        print("Completed ~ @depth: %s%s  (%d)" % ("".join(["   " for i in range(0, 15 - depth)]), depth, time.time() - start_t))
        return simplified, next_var_id

    # An OR. Simplify all the sub-formulae first.
    # It needs to be this fancy in case ids change as sub-formulae are simplified.
    # Even the CURRENT formula could change.
    for sub_f in bf.get_contents():
        simplified, next_var_id = advanced_simplify_boolean_formula(sub_f, filename, bfb, assignments_bank, var_ids, next_var_id, depth+1)
        assignments_bank[sub_f.get_id()] = assignments_bank[simplified.get_id()]
    """
    contents = bf.get_contents()
    contents_copy = list(contents)
    for i in range(0, len(contents)):
        sub_f = contents[i]
        prev_id = sub_f.get_id()
        simplified, next_var_id = advanced_simplify_boolean_formula(sub_f, filename, bfb, assignments_bank, var_ids, next_var_id, depth+1)
        new_id = simplified.get_id()
        if new_id not in assignments_bank:
            raise ValueError("Error. New formula not given an id.")
            # assignments_bank[new_id] = assignments_bank[prev_id]
        contents_copy[i] = simplified
    bf = bfb.gen_op_formula(bf.get_type(), contents_copy)
    """
    """
    completed = set()
    anything_unexpected = False
    while len(completed) != len(bf.get_contents()):
        contents = bf.get_contents()
        for sub_f in contents:
            if sub_f.get_id() not in completed:
                simplified, next_var_id = advanced_simplify_boolean_formula(sub_f, filename, bfb, assignments_bank, var_ids, next_var_id, depth+1)
                if sub_f.get_id() in bfb.id_to_formula:
                    # bfb.replace_all_occurrences_of_formula(sub_f, simplified)
                    bf = bfb.get_formula_from_external_label(the_label)
                else:
                    print("This is unexpected.")
                    anything_unexpected = True
                completed.add(simplified.get_id())
                break
    """

    # If, in the process of all this simplification, the current formula ceased to be an and or an or, handle those seperately:
    if bf.get_type() != BF_AND and bf.get_type() != BF_OR:
        print("Eh?")
        return advanced_simplify_boolean_formula(bf, filename, bfb, assignments_bank, var_ids, next_var_id, depth)

    if bf.get_type() == BF_OR:
        # An or of ors of ands
        satisfying_assignments_for_sub_fs = []
        for sub_f in bf.get_contents():
            satisfying_assignments_for_sub_fs += assignments_bank[sub_f.get_id()]
        # Get the minimized assignments for combo of the sub-formulae.
        assignments = assignments_from_assignments(satisfying_assignments_for_sub_fs, var_ids, filename, negated=False)
        # Get the formula for these new negated assignments.
        simplified = formula_from_assignments(assignments, var_ids, filename, bfb, negated=False)
        assignments_bank[simplified.get_id()] = assignments
        print("Completed OR @dpth: %s%s  (%d)" % ("".join(["   " for i in range(0, 15 - depth)]), depth, time.time() - start_t))
        return simplified, next_var_id

    raise ValueError("The formula was supposed to have all ANDs flushed out!")
    # formula is an and
    # the assignments arrays for the sub_fs are ors of ands.
    # So, effectively, we have an and of ors of ands.

    # The strategy: Consider the negation of the clause.
    # F = and-of-or-of-ands
    # not F = or-of-not-(or-of-ands)
    # solving for these not-(or-of-ands) by using negated=True, we can get
    #  some plain-old or-of-ands
    # Then we have an or-of-or-of ands. Huzzah!

    # Then add constraints that conflicting
    #  clauses cannot both be true (i.e. filter out some of the truth lines).
    # Run espresso on this sub-problem. Get back the "assignments" and use these to create
    #  valid assignments.
    # Then run espresso again on the actual assignments.

def formula_from_assignments(satisfying_assignments, var_ids, filename, bfb, negated=False):
    create_espresso_input_file(satisfying_assignments, var_ids, filename, negated=negated)
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
    return simplified

def assignments_from_assignments(satisfying_assignments, var_ids, filename, negated=False):
    idx_to_var_name = create_espresso_input_file(satisfying_assignments, var_ids, filename, negated=negated)
    proc = subprocess.Popen(["./espresso_binaries/espresso", filename],
                          stdout=subprocess.PIPE)
    output, error = proc.communicate()
    if sys.version_info[0] == 3:
        output = output.decode()
    lines = output.split("\n")[6:-2]

    new_assignments = []
    for line in lines:
        new_assignment = []
        for i in range(0, len(idx_to_var_name)):
            char = line[i]
            if char == "1":
                new_assignment.append((var_ids[idx_to_var_name[i]], True))
            elif char == "0":
                new_assignment.append((var_ids[idx_to_var_name[i]], False))
            elif char != "-":
                print("Unexpected character! `%s`" % char)
        new_assignments.append(new_assignment)
    return new_assignments

def create_espresso_input_file(satisfying_assignments, var_ids, filename, negated=False):
    id_to_var = {i: v for v, i in var_ids.items()}
    relevant_id_to_var = {}
    for assignment in satisfying_assignments:
        for (i, _) in assignment:
            relevant_id_to_var[i] = id_to_var[i]

    id_to_idx = sorted([i for i, var in relevant_id_to_var.items()])
    id_to_idx = {id_to_idx[idx]: idx for idx in range(0, len(id_to_idx))}
    idx_to_var = {idx: id_to_var[i] for i, idx in id_to_idx.items()}

    f = open(filename, "w")
    f.write(".i %d\n" % len(relevant_id_to_var)) # Number of inputs
    f.write(".o 1\n") # 1 output
    var_names_in_order = [" %s" % idx_to_var[i] for i in range(0, len(idx_to_var))]
    f.write(".ilb %s\n" % "".join(var_names_in_order))
    f.write(".ob OUTPUT\n") # Name of output.
    f.write(".phase %d\n" % (1 - int(negated)))

    for assignment in satisfying_assignments:
        assignment_array = ["-" for var in range(0, len(relevant_id_to_var))]
        for (var_id, true_or_false) in assignment:
            if true_or_false:
                assignment_array[id_to_idx[var_id]] = "1"
            else:
                assignment_array[id_to_idx[var_id]] = "0"
        assignment_array.append(" 1\n")
        f.write("".join(assignment_array))

    f.write(".e\n")
    f.close()
    return [x[1:] for x in var_names_in_order]

"""
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

        negate_assignments(sub_assignments)

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
"""

def negate_assignments(assignments):
    # Not of or of ands <-> and of or of nots
    # Want to get back to or of ands
    full_var_set = set()
    full_var_assign_set = set()
    for assignment in assignments:
        for (var, true_or_false) in assignment:
            full_var_set.add(var)
            full_var_assign_set.add((var, not true_or_false)) # Negation of variables' assignment.

    var_to_clauses = {var: set() for var in full_var_set}
    var_assign_to_clauses = {x: set() for x in full_var_assign_set}
    for i in range(0, len(assignments)):
        for (var, true_or_false) in assignment:
            var_to_clauses

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

d2 = simplify_boolean_formula(d)
print(d2.to_string(with_spaces=True))

f = open("./saved_5_nn_formulae.txt")
first_formula = f.readline()
if first_formula[-1] == "\n":
    first_formula = first_formula[0:-1]
orig = BFB.gen_formula_from_string(first_formula)
print("The original formula had %d characters" % len(orig.to_string(with_spaces=False)))
simplified = simplify_boolean_formula(orig, bfb=BFB)
print("The simplified formula had %d characters" % len(simplified.to_string(with_spaces=False)))
