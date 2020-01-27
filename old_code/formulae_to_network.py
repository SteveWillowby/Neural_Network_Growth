from network_dag import *
from boolean_formula import *
from overlapped_formulae import *
from scipy.optimize import linprog
import random
import math
import warnings

warnings.filterwarnings('ignore', '.*conditioned matrix.*')
warnings.filterwarnings('ignore', '.*if you see this frequently.*')

def formulae_to_network(formulae, var_thresh=1.5):
    overlapped = BooleanFormulaeOverlapped(formulae) 
    return bfo_to_network(overlapped, var_thresh)

def bfo_to_network(bfo, var_thresh):
    int_nodes = bfo.get_intermediate_nodes()
    out_nodes = bfo.get_output_nodes()
    lit_nodes = bfo.get_literal_nodes()

    output_sort_order = dict(bfo.output_labels)

    new_network = NetworkDAG()

    # Add the inputs to the NetworkDAG
    for i in range(0, 784):
        new_network.add_input(i)

    # TODO: Make search occur in random order
    iters = 0
    prev_num_outputs = 10
    while len(int_nodes) > 0 or len(out_nodes) > 0:
        iters += 1
        if iters % 100 == 0:
            print(iters)
        found_one = False
        if len(out_nodes) < prev_num_outputs:
            print("Outputs Decreased! %d vs %d" % (len(out_nodes), prev_num_outputs))
            prev_num_outputs = len(out_nodes)
        for int_node in int_nodes:
            can_convert, weight_assignment, bias = evaluate_or_of_ands(bfo, int_node, lower=-var_thresh, upper=var_thresh) #TODO: add modified threshold for output
            if can_convert:
                new_network.add_hidden(int_node, bias)
                # print("Adding hidden unit %d" % int_node)
                # print(weight_assignment)
                for variable_id, weight in weight_assignment.items():
                    new_network.add_edge(variable_id, int_node, weight)
                found_one = True
                # print("Or of ands -- INT")
                collapse_node(bfo, int_node)
                break
        if not found_one:
            for out_node in out_nodes:
                if out_node in bfo.literal_sets:
                    can_convert, weight_assignment, bias = LP_vals_for_flat(bfo, out_node, lower=-var_thresh, upper=var_thresh)
                    if can_convert:
                        print("flat node -- OUT")
                else:
                    can_convert, weight_assignment, bias = evaluate_or_of_ands(bfo, out_node, lower=-var_thresh, upper=var_thresh)
                    if can_convert:
                        print("Or of ands -- OUT")
                if can_convert:
                    new_network.add_output(out_node, bias)
                    print("Adding output unit %d" % out_node)
                    # print(weight_assignment)
                    for variable_id, weight in weight_assignment.items():
                        new_network.add_edge(variable_id, out_node, weight)
                    found_one = True
                    collapse_node(bfo, out_node)
                    break
        if not found_one:
            best_parent_count = 0
            best_lit = None
            for lit_node in lit_nodes:
                parents = bfo.get_parents(lit_node)
                if len(parents) > best_parent_count and len(bfo.literal_sets[lit_node]) > 1:
                    best_parent_count = len(parents)
                    best_lit = lit_node
            if best_lit is None:
                print("ERROR! Did not find any BFO node to collapse!")
                exit(1)
            parents = bfo.get_parents(best_lit)
            success, weight_assignment, bias = LP_vals_for_flat(bfo, best_lit, lower=-var_thresh, upper=var_thresh)
            if not success:
                print("SERIOUS ERROR! Conversion of flat %s node (%s) failed!" % (op, best_lit))
                exit(1)
            new_network.add_hidden(best_lit, bias)
            # print("Adding FLAT hidden unit %d" % best_lit)
            # print(weight_assignment)
            for variable_id, weight in weight_assignment.items():
                new_network.add_edge(variable_id, best_lit, weight)
            # print("Flat node -- %s" % op)
            collapse_node(bfo, best_lit)

    print(new_network.get_output_nodes())
    print(output_sort_order)

    return new_network, output_sort_order


# Determines whether or not a node can be a valid or of ands.
# If not, returns False, None, None
# Is so, returns True, weight_assignment, bias
# 
# the weight assignment is a dict mapping the variable (not literal) to its weight
def evaluate_or_of_ands(bfo, node, lower, upper):
    if bfo.get_op(node) != bfo.OR:
        return False, None, None
    literals = bfo.get_literal_nodes()
    for child in bfo.get_children(node):
        if child not in literals:
            return False, None, None

    clause_ids = bfo.get_children(node)
    clauses = [bfo.literal_sets[clause] for clause in clause_ids]
    all_literals = set(clauses[0])
    for i in range(1, len(clauses)):
        all_literals |= clauses[i]
    positive_literals = set()
    negative_literals = set()
    for (variable, true_or_false) in all_literals:
        if true_or_false:
            positive_literals.add(variable)
        else:
            negative_literals.add(variable)

    if len(positive_literals & negative_literals) > 0:
        return False, None, None

    # TODO: consider switching to cycle detection
    return LP_vals_for_or_of_ands(bfo, clauses, positive_literals, negative_literals, lower=lower, upper=upper)

# Helper function for evaluate_or_of_ands
def LP_vals_for_or_of_ands(bfo, clauses, positive_lits, negative_lits, lower=-0.75, upper=0.75):
    positive_lits = list(positive_lits)
    positive_lits.sort()
    negative_lits = list(negative_lits)
    negative_lits.sort()

    next_idx = 0
    lit_indices = {}
    for p_var in positive_lits:
        lit_indices[p_var] = next_idx
        next_idx += 1
    for n_var in negative_lits:
        lit_indices[n_var] = next_idx
        next_idx += 1

    c = [1.0 for i in range(0, len(positive_lits))] + [-1.0 for i in range(0, len(negative_lits))] + [0.0]
    A = []
    b = []
    for clause in clauses:
        clause_vars = set([v for (v, tf) in clause])
        a = []
        for lit in positive_lits:
            if lit in clause_vars:
                a.append(-1.0)
            else:
                a.append(0.0)
        for lit in negative_lits:
            if lit in clause_vars:
                a.append(0.0)
            else:
                a.append(-1.0)
        a.append(-1.0)

        A.append(a)
        b.append(-1.0 * upper)

        a_base = [-j for j in a]
        for special_lit in positive_lits:
            if special_lit in clause_vars:
                a_copy = list(a_base)
                a_copy[lit_indices[special_lit]] = 0.0
                A.append(a_copy)
                b.append(lower)
        for special_lit in negative_lits:
            if special_lit in clause_vars:
                a_copy = list(a_base)
                a_copy[lit_indices[special_lit]] = 1.0
                A.append(a_copy)
                b.append(lower)

    bounds = [(0.0, None) for lit in positive_lits] + [(None, 0.0) for lit in negative_lits] + [(None, None)]
    #print("Starting linprog")
    result = linprog(c, A_ub=A, b_ub=b, method="interior-point", options={"disp":False, \
        "maxiter":500, "presolve":True}, bounds=bounds) #, "lstq", "tol", "maxiter":N*N*N*N*100}) #method="interior-point"
    if result.success:
        lit_weights = {}
        for i in range(0, len(positive_lits)):
            lit_weights[positive_lits[i]] = result.x[i]
        for i in range(0, len(negative_lits)):
            lit_weights[negative_lits[i]] = result.x[len(positive_lits) + i]
        bias = result.x[-1]
        #print("Success!")
        #print(result.fun)
        #print(["%.1f" % v for v in result.x])
        return True, lit_weights, bias
    #print("Failure!")
    #print(result.status)
    #print(result.nit)
    #print(result.fun)
    #print(result.message)
    #print(["%.1f" % v for v in result.x])

    return False, None, None

def LP_vals_for_flat(bfo, node_id, lower=-0.75, upper=0.75):
    op = bfo.get_op(node_id)
    literals = bfo.literal_sets[node_id]
    positive_lits = set()
    negative_lits = set()
    for (lit, true_or_false) in literals:
        if true_or_false:
            positive_lits.add(lit)
        else:
            negative_lits.add(lit)
    weight_assignment = None
    bias = None
    if op == bfo.AND:
        success, weight_assignment, bias = LP_vals_for_and(positive_lits, negative_lits, lower=lower, upper=upper)
    else:
        success, weight_assignment, bias = LP_vals_for_or(positive_lits, negative_lits, lower=lower, upper=upper)
    return success, weight_assignment, bias

def LP_vals_for_and(positive_lits, negative_lits, lower=-0.75, upper=0.75):
    positive_lits = list(positive_lits)
    positive_lits.sort()
    negative_lits = list(negative_lits)
    negative_lits.sort()

    c = [1.0 for i in range(0, len(positive_lits))] + [-1.0 for i in range(0, len(negative_lits))] + [0.0]
    A = []
    b = []
    a = []
    for lit in positive_lits:
        a.append(-1.0)
    for lit in negative_lits:
        a.append(0.0)
    a.append(-1.0)

    A.append(a)
    b.append(-1.0 * upper)

    a_base = [-j for j in a]
    for special_lit_idx in range(0, len(positive_lits)):
        a_copy = list(a_base)
        a_copy[special_lit_idx] = 0.0
        A.append(a_copy)
        b.append(lower)
    for special_lit_idx in range(len(positive_lits), len(positive_lits) + len(negative_lits)):
        a_copy = list(a_base)
        a_copy[special_lit_idx] = 1.0
        A.append(a_copy)
        b.append(lower)

    bounds = [(0.0, None) for lit in positive_lits] + [(None, 0.0) for lit in negative_lits] + [(None, None)]
    result = linprog(c, A_ub=A, b_ub=b, method="interior-point", options={"disp":False}, bounds=bounds) #, "maxiter":N*N*N*N*100})
    if result.success:
        lit_weights = {}
        for i in range(0, len(positive_lits)):
            lit_weights[positive_lits[i]] = result.x[i]
        for i in range(0, len(negative_lits)):
            lit_weights[negative_lits[i]] = result.x[len(positive_lits) + i]
        bias = result.x[-1]
        return True, lit_weights, bias
    else:
        print(result)

    return False, None, None

def LP_vals_for_or(positive_lits, negative_lits, lower=-0.75, upper=0.75):
    positive_lits = list(positive_lits)
    positive_lits.sort()
    negative_lits = list(negative_lits)
    negative_lits.sort()

    c = [1.0 for i in range(0, len(positive_lits))] + [-1.0 for i in range(0, len(negative_lits))] + [0.0]
    A = []
    b = []
    a = [0.0 for i in positive_lits] + [1.0 for i in negative_lits] + [1.0]

    A.append(a)
    b.append(lower)

    for special_lit_idx in range(0, len(positive_lits)):
        a_copy = list(a)
        a_copy[special_lit_idx] = 1.0
        A.append(a_copy)
        b.append(upper)
    for special_lit_idx in range(len(positive_lits), len(positive_lits) + len(negative_lits)):
        a_copy = list(a)
        a_copy[special_lit_idx] = 0.0
        A.append(a_copy)
        b.append(upper)

    bounds = [(0.0, None) for lit in positive_lits] + [(None, 0.0) for lit in negative_lits] + [(None, None)]
    result = linprog(c, A_ub=A, b_ub=b, method="interior-point", options={"disp":False}, bounds=bounds) #, "maxiter":N*N*N*N*100})
    if result.success:
        lit_weights = {}
        for i in range(0, len(positive_lits)):
            lit_weights[positive_lits[i]] = result.x[i]
        for i in range(0, len(negative_lits)):
            lit_weights[negative_lits[i]] = result.x[len(positive_lits) + i]
        bias = result.x[-1]
        return True, lit_weights, bias

    return False, None, None

# Given a node id, converts that node into a literal in the bfo.
def collapse_node(bfo, node_id):
    parents = set(bfo.get_parents(node_id))
    children = set(bfo.get_children(node_id))
    if len(parents) == 0:
        outputs = bfo.get_output_nodes()
        if node_id not in outputs:
            print("ERROR! Somehow this node (%s) has no parents yet is not an output!" % node_id)
        bfo.delete_node(node_id)
        return

    outputs = bfo.get_output_nodes()
    literals = bfo.get_literal_nodes()
    intermediates = bfo.get_intermediate_nodes()

    bfo.delete_node(node_id)
    new_lit = (node_id, True)
    new_not_lit = (node_id, False)
    new_id = bfo.add_literals(set([new_lit]), bfo.AND)
    new_not_id = bfo.add_literals(set([new_not_lit]), bfo.AND)

    # Handle connections to children (delete them if no connections remain)
    for child in children:
        if len(bfo.get_parents(child)) == 0:
            if child in bfo.get_output_nodes():
                print("Somehow an output is a child of something else!")
            bfo.delete_node(child)

    # Handle connections to parents, including performing flattenings
    for parent in parents:
        parent_op = bfo.get_op(parent)
        if parent_op == bfo.NOT:
            grandparents = set(bfo.get_parents(parent))
            if parent in outputs:
                print("A BFO output with NOT as its op!")
            bfo.delete_node(parent)
            for grandparent in grandparents:
                if should_flatten(bfo, grandparent):
                    flatten(bfo, grandparent, extra_literal=new_not_lit)
                else:
                    bfo.add_edge(grandparent, new_not_id)
        else:
            if should_flatten(bfo, parent):
                flatten(bfo, parent, extra_literal=new_lit)
            else:
                bfo.add_edge(parent, new_id)

# Assumes that a connection to a single literal is missing.
def should_flatten(bfo, node_id):
    literals = bfo.get_literal_nodes()
    if node_id in literals:
        return False
    if bfo.get_op(node_id) == bfo.NOT: # Ideally this check would not be necessary.
        print("Uh-Oh! Checked to see if a NOT node should be flattened! This is unexpected and suggests a double-negative.")
        return False
    num_children = len(bfo.get_children(node_id))
    #if ignore is not None:
    #    num_children -= 1
    for child in bfo.get_children(node_id):
        if child not in literals:
            return False
        if len(bfo.literal_sets[child]) > 1:
            return False
    return True

# Extra_literal should be in the tuple format (str_id, True/False)
# Returns the new node id
def flatten(bfo, node_id, extra_literal=None):
    parents = set(bfo.get_parents(node_id))
    children = set(bfo.get_children(node_id))
    all_literals = set()
    if extra_literal is not None:
        all_literals.add(extra_literal)
    a_child_op = None
    for child in children:
        a_child_op = bfo.get_op(child)
        lits = bfo.literal_sets[child]
        if len(lits) > 1 and len(children) > 1:
            print("ERROR! Flattening parent w/ > 1 children, at least one of which is a multi-literal set!")
            exit(1)
        all_literals |= lits
    op = bfo.get_op(node_id)
    if len(children) == 1: # If and of a single or, should be or, and vice versa
        op = a_child_op

    for child in children:
        if len(bfo.get_parents(child)) == 1:
            bfo.delete_node(child)
            if child in bfo.get_output_nodes():
                print("Somehow an output is a child of something else! (case B)")

    if node_id in bfo.get_output_nodes():
        bfo.literal_sets[node_id] = set(all_literals)
        bfo.ops[node_id] = op
        return

    bfo.delete_node(node_id)

    new_id = bfo.add_literals(set(all_literals), op)
    for parent in parents:
        bfo.add_edge(parent, new_id)
