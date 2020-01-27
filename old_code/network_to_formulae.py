from network_dag import *
from boolean_formula import *

# Interface:
#   Given a neural network, outputs a dictionary mapping output names to boolean formula
#   network_to_formulae(network)

# Returns all sets of variables summing to >= threshold such that if any value is removed, sum < threshold
# ASSUMES weighted_vars in order of decreasing weight
def get_clauses_from_vars_and_threshold(weighted_vars, threshold):
    if threshold < 0:
        print("JUSTUS MADE A MISTAKE! threshold SHOULD NOT BE BELOW ZERO IN THIS FUNCTION!")
        exit(1)
    if len(weighted_vars) == 0:
        print("JUSTUS MADE A MISTAKE! len(weighted_vars) SHOULD NOT BE ZERO IN THIS FUNCTION!")
        exit(1)

    with_clauses = []
    if weighted_vars[0][1] >= threshold:
        with_clauses.append(weighted_vars[0][0])
    elif len(weighted_vars) > 1: # If there are more variables
        sub_clauses = get_clauses_from_vars_and_threshold(weighted_vars[1:], threshold - weighted_vars[0][1])
        for sub_clause in sub_clauses:
            with_clauses.append(sub_clause + " && %s" % (weighted_vars[0][0]))

    without_clauses = []
    if len(weighted_vars) > 1:
        without_clauses = get_clauses_from_vars_and_threshold(weighted_vars[1:], threshold)

    return with_clauses + without_clauses

#c = get_clauses_from_vars_and_threshold([("4a", 4), ("4b", 4), ("3", 3), ("2", 2), ("1", 1)], 8)
#for v in c:
#    print(v)

def network_to_formulae(network, output_threshold=0.0, MAX_INPUTS_PER_NEURON=10):

    net_outputs = network.get_output_nodes()
    net_inputs = network.get_input_nodes()
    net_non_inputs = network.get_output_nodes() | network.get_hidden_nodes()
    biases = network.get_biases()

    all_neurons = {}

    filler_for_bad_nodes = net_inputs.pop() # Hacky -- if a node always fires (or never fires), replace it with this input.
    net_inputs.add(filler_for_bad_nodes)
    filler_formula = BooleanFormula()
    filler_formula.init_from_string(str(filler_for_bad_nodes))

    print("Beginning conversion at a node-level.")
    # For each node, find the minimal clauses that must be true to satisfy it (i.e. a DNF formula)
    for node in net_non_inputs:
        node_str = str(node)
        # print("Node! %s" % node)
        weighted_inputs = network.get_parents_with_weights(node)
        if len(weighted_inputs) == 0:
            print("A non-input node with no inputs to it found! Error! (Node: %s)" % node)
            exit(1)

        bias_offset = 0
        if len(weighted_inputs) > MAX_INPUTS_PER_NEURON: # Reduce the list to the max number of neurons
            print("Node %s has too many inputs (%d). Using only the top %d." % (node, len(weighted_inputs), MAX_INPUTS_PER_NEURON))
            weighted_inputs_list = [(abs(w), w, p) for (p, w) in weighted_inputs]
            weighted_inputs_list.sort(reverse=True)
            bias_offset = sum([-x[1] / 2.0 for x in weighted_inputs_list[MAX_INPUTS_PER_NEURON:]]) # / 2.0 to treat nodes as equally likely to fire/not fire
            weighted_inputs_list = weighted_inputs_list[0:MAX_INPUTS_PER_NEURON]
            weighted_inputs = [(x[2], x[1]) for x in weighted_inputs_list]
            
        threshold = -biases[node] + bias_offset

        if node in net_outputs:
            threshold += output_threshold

        inputs = []
        for (p, w) in weighted_inputs:
            if w < 0:
                inputs.append((-w, "~%s" % p))
                threshold += -w
            else:
                inputs.append((w, "%s" % p))

        if threshold <= 0: # If node always "fires"
            print("Threshold is <= 0! This should never happen! Ignoring this node (%s) and carrying on." % node)
            all_neurons[node_str] = filler_formula
            continue

        if threshold > sum([w for (w, p) in inputs]):
            print("Node never \"fires!\" This should never happen! Ignoring this node (%s) and carrying on." % node)
            all_neurons[node_str] = filler_formula
            continue

        # Order nodes in decreasing order of absolute value of weight
        inputs.sort(reverse=True)
        inputs = [(y, x) for (x, y) in inputs]
        clauses = get_clauses_from_vars_and_threshold(inputs, threshold)
        full_dnf = "(%s)" % clauses[0]
        for i in range(1, len(clauses)):
            full_dnf += (" || (%s)" % clauses[i])

        neuron = BooleanFormula()
        neuron.init_from_string(full_dnf)
        all_neurons[node_str] = neuron

    node_order = network.topological_sort_order(top_to_bottom=True)

    print("Composing Larger Formulae Via Variable Substitution...")
    
    net_input_strs = set([str(n) for n in net_inputs])
    net_non_inputs_strs = set([str(n) for n in net_non_inputs])

    skipped = 0
    replaced = 0
    for node in node_order:
        node_str = str(node)
        if node in net_non_inputs:
            formula = all_neurons[node_str]
            formula_vars = formula.get_variables_risky()
            for var_str in formula_vars:
                if var_str in net_non_inputs_strs:
                    replaced += 1
                    formula.shallow_replace_variable(var_str, all_neurons[var_str])
                else:
                    if var_str not in net_input_strs:
                        print("ALERT! SKIPPING %s! We don't know why!" % var_str)
                    skipped += 1
    print("Replaced %d | Skipped %d" % (replaced, skipped))

    return {output: all_neurons[str(output)] for output in net_outputs}

"""
N = NetworkDAG()
N.add_input("i1")
N.add_input("i2")
N.add_input("i3")
N.add_hidden("h1", -1.0)
N.add_output("o1", -2.0)
N.add_output("o2", -1.5)
N.add_edge("i1", "h1", 1.0)
N.add_edge("i2", "h1", 2.0)
N.add_edge("i3", "h1", -1.0)
N.add_edge("i1", "o1", 1.0)
N.add_edge("i2", "o1", 2.0)
N.add_edge("h1", "o1", -1.0)
N.add_edge("i1", "o2", 1.0)
N.add_edge("i2", "o2", -0.5)
N.add_edge("h1", "o2", 2.0)
res = network_to_formulae(N)
for output, formula in res.items():
    print("%s: %s" % (output, formula.to_string()))
    formula.sort()
    print("%s: %s" % (output, formula.to_string()))
"""
