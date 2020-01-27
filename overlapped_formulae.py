from network_dag import *
from boolean_formula import *
from network_to_formulae import *

#    get_output_nodes()
#    get_literal_nodes()
#    get_intermediate_nodes()

#    get_edges()

#    get_children(id_num)
#    get_parents(id_num)
#    get_op(id_num)

#    The following three functions return an assigned id num
#    add_literals(literal_set, op)
#    add_intermediate(op, children=[])
#    add_output(name, op, children=None, literal_set=None)

#    delete_node(id_num)

#    add_edge(parent, child, check_no_cycle=False)
#    delete_edge(parent, child)

#    topological_sort_order(top_to_bottom=False)

class BooleanFormulaeOverlapped:

    def __init__(self, formulae):
        formulae = dict(formulae)

        self.output_nodes = set()
        self.output_labels = {}
        self.literal_nodes = set()
        self.intermediate_nodes = set()
        self.all_nodes = set()
        self.edges = set()
        self.children = {}
        self.parents = {}

        self.literal_sets = {} # Each literal is a tuple, (var, negation-status [i.e. False if negated])
        self.ops = {}
        f = None
        for output, f1 in formulae.items():
            f = f1
            break
        self.AND = f.AND
        self.OR = f.OR
        self.NOT = f.NOT
        self.VARIABLE = f.VARIABLE
        self.LITERAL_STR = "lit_str:"
        self.AND_STR = "and_str:"
        self.OR_STR = "or_str:"
        self.NOT_STR = "not_str:"
        self.OUTPUT_STR = "output_str:"

        self.str_ids_to_num_ids = {}
        self.next_node_id = 784 # Make sure these ids don't conflict with actual input ids

        self.recursive_constructor(formulae)

    def get_output_nodes(self):
        return self.output_nodes
    def get_literal_nodes(self):
        return self.literal_nodes
    def get_intermediate_nodes(self):
        return self.intermediate_nodes

    def get_op(self, id_num):
        return self.ops[id_num]

    # Returns the set of all edges in the network: (parent, child, weight)
    def get_edges(self):
        return set(self.edges)

    def get_children(self, id_num):
        if id_num not in self.all_nodes:
            print("ERROR: (BFO) node %s not in network" % id_num)
            exit(1)
        return set(self.children[id_num])

    def get_parents(self, id_num):
        if id_num not in self.all_nodes:
            print("ERROR: (BFO) node %s not in network" % id_num)
            exit(1)
        return set(self.parents[id_num])

    def add_output(self, name, op, children=None, literal_set=None):
        if children is not None and literal_set is not None:
            print("ERROR! (BFO) Cannot have output node with literals AND children!")
            exit(1)
        self.output_nodes.add(self.next_node_id)
        self.output_labels[self.next_node_id] = name
        self.all_nodes.add(self.next_node_id)
        self.parents[self.next_node_id] = set()
        self.children[self.next_node_id] = set()
        self.ops[self.next_node_id] = op
        if children is not None:
            for child in children:
                self.add_edge(self.next_node_id, child)
        if literal_set is not None:
            self.literal_sets[self.next_node_id] = literal_set
        self.next_node_id += 1
        return self.next_node_id - 1

    def add_literals(self, literal_set, op):
        self.literal_nodes.add(self.next_node_id)
        self.all_nodes.add(self.next_node_id)
        self.parents[self.next_node_id] = set()
        self.children[self.next_node_id] = set()
        self.literal_sets[self.next_node_id] = literal_set
        self.ops[self.next_node_id] = op
        self.next_node_id += 1
        return self.next_node_id - 1

    def add_intermediate(self, op, children=[]):
        self.intermediate_nodes.add(self.next_node_id)
        self.all_nodes.add(self.next_node_id)
        self.parents[self.next_node_id] = set()
        self.children[self.next_node_id] = set()
        self.ops[self.next_node_id] = op
        for child in children:
            self.add_edge(self.next_node_id, child)
        self.next_node_id += 1
        return self.next_node_id - 1

    def delete_node(self, id_num):
        if id_num not in self.all_nodes:
            print("ERROR: (BFO) node %s not in the network" % id_num)
            exit(1)
        for c in self.children[id_num]:
            self.edges.remove((id_num, c))
            self.parents[c].remove(id_num)
        for p in self.parents[id_num]:
            self.edges.remove((p, id_num))
            self.children[p].remove(id_num)
        del self.children[id_num]
        del self.parents[id_num]

        self.all_nodes.remove(id_num)
        if id_num in self.output_nodes:
            print("Deleting an output!")
            self.output_nodes.remove(id_num)
            del self.output_labels[id_num]
        elif id_num in self.literal_nodes:
            self.literal_nodes.remove(id_num)
        else:
            self.intermediate_nodes.remove(id_num)

    def add_edge(self, parent, child, check_no_cycle=False):
        if parent not in self.all_nodes:
            print("ERROR: (BFO) node %s not in network" % parent)
            exit(1)
        if child not in self.all_nodes:
            print("ERROR: (BFO) node %s not in network" % child)
            exit(1)
        if child in self.children[parent]:
            print("ERROR: (BFO) edge (%s, %s) already exists" % (parent, child))
            exit(1)
        if child == parent:
            print("ERROR: (BFO) cannot create an edge from a node to itself (%s, %s)" % (parent, child))
            exit(1)
        if child in self.output_nodes:
            print("ERROR: (BFO) cannot create an edge pointing to an output (%s, %s)" % (parent, child))
            exit(1)
        if parent in self.literal_nodes:
            print("ERROR: (BFO) cannot create an edge coming from an literal node (%s, %s)" % (parent, child))
            exit(1)
        if check_no_cycle:
            if self.a_ancestor_b(child, parent):
                print("ERROR: (BFO) attempted to create a cycle by adding edge (%s, %s)" % (parent, child))
                exit(1)
        self.edges.add((parent, child))
        self.children[parent].add(child)
        self.parents[child].add(parent)

    def a_ancestor_b(self, a, b):
        the_stack = [a]
        while len(the_stack) > 0:
            node = the_stack.pop()
            if node == b:
                return True
            for c in self.children[node]:
                the_stack.append(c)
        return False

    def topological_sort_order(self, top_to_bottom=False):
        sortable_nodes = [TopoSortHelperClass(id_num, self) for id_num in self.all_nodes]
        sortable_nodes.sort(reverse=top_to_bottom)
        return [tshc.n for tshc in sortable_nodes]

    def delete_edge(self, parent, child):
        if (parent, child) not in self.edges:
            print("ERROR: (BFO) edge (%s, %s) does not exist" % (parent, child))
            exit(1)
        del self.parents[child][parent]
        del self.children[parent][child]
        del self.edges[(parent, child)]

    def recursive_constructor(self, formulae):
        already_seen_ptrs = {}
        for output, formula in formulae.items():
            self.recursive_constructor_helper(formula, already_seen_ptrs, is_an_output=output)

        print("\nConstructed overlapped formulae DAG with the following statistics:")
        print("Number of literals nodes: %d" % len(self.get_literal_nodes()))
        print("Number of intermediate nodes: %d" % len(self.get_intermediate_nodes()))
        print("Number of output nodes: %d" % len(self.get_output_nodes()))
        print("Number of edges: %d\n" % len(self.get_edges()))

    def recursive_constructor_helper(self, formula, already_seen_ptrs, is_an_output=None):
        id_str = None
        node_is_literal_set = True
        edges = []
        literals = set()
        op = self.AND
        node_id = None

        # MAIN STEP 1: Find the ID of the current formula:

        if formula.f[0] == self.VARIABLE: # It's a non-negated literal!
            id_str = "%s%s" % (self.LITERAL_STR, formula.f[1])
            var_num = int(formula.f[1])
            if var_num > 783:
                print("Variable found when constructing bfo with id > 783! (%d)" % var_num)
                var_num = 783
            literals = set([(var_num, True)])
        elif formula.f[0] == self.NOT and formula.f[1].f[0] == self.VARIABLE: # It's a negated literal!
            id_str = "%s~%s" % (self.LITERAL_STR, formula.f[1].f[1])
            var_num = int(formula.f[1].f[1])
            if var_num > 783:
                print("Variable found when constructing bfo with id > 783! (%d)" % var_num)
                var_num = 782
            literals = set([(var_num, False)])
        else:
            op = formula.f[0]
            for i in range(1, len(formula.f)):
                if formula.f[i] in already_seen_ptrs:
                    formula.f[i] = already_seen_ptrs[formula.f[i]]
                else:
                    ref = formula.f[i]
                    formula.f[i] = self.recursive_constructor_helper(formula.f[i], already_seen_ptrs)
                    already_seen_ptrs[ref] = formula.f[i]
            f_copy = list(set(formula.f[1:]))
            if len(f_copy) < len(formula.f) - 1 and len(f_copy) == 1:
                print("WHOLE clause consists of a duplicated literal! Oh no! %s This may cause a code failure (node id is %d)." % (formula.f[1:], self.next_node_id))
            f_copy.sort()
            id_str = ""
            for f_sub_id in f_copy:
                id_str += ",%s" % f_sub_id
            all_literals = True
            for f_sub_id in f_copy:
                if f_sub_id in self.intermediate_nodes or len(self.literal_sets[f_sub_id]) > 1:
                    all_literals = False
                    break
            if not all_literals:
                node_is_literal_set = False
                edges = f_copy
            else:
                for f_sub_id in f_copy:
                    lit = self.literal_sets[f_sub_id].pop()
                    if len(self.literal_sets[f_sub_id]) > 0:
                        print("JUSTUS IS CONFUSED! HELP HIM WITH LITERALS!")
                    self.literal_sets[f_sub_id].add(lit)
                    literals.add(lit)

        # MAIN STEP 2: If this is a new node, add it to our DAG.

        if is_an_output is not None: # If the node is an output
            id_str = "%s%s:%s" % (self.OUTPUT_STR, is_an_output, id_str)

        if id_str in self.str_ids_to_num_ids:
            node_id = self.str_ids_to_num_ids[id_str]
        else:
            node_id = self.next_node_id
            self.str_ids_to_num_ids[id_str] = node_id
            if node_is_literal_set:
                if is_an_output is not None:
                    self.add_output(is_an_output, op, literal_set = literals)
                    print(is_an_output)
                else:
                    self.add_literals(literals, op)
            elif is_an_output is not None: # We're at the base node -- it's an output!
                self.add_output(is_an_output, op, children=edges)
                print(is_an_output)
            else:
                self.add_intermediate(op, children=edges)

        return node_id

    """
    def hideous_constructor(self, formulae):
        # I apologize for the next 70 or so lines of code. This should have been written recursively.
        for output, formula in formulae.items():
            stack = [[formula, 1]]
            while len(stack) > 0:
                curr_formula = stack[-1]
                id_str = None
                node_is_literal_set = True
                edges = []
                literals = set()
                op = self.AND
                node_id = None
                if curr_formula[0].f[0] == self.VARIABLE: # It's a non-negated literal!
                    id_str = "%s%s" % (self.LITERAL_STR, curr_formula[0].f[1])
                    literals = set([(int(curr_formula[0].f[1]), True)])
                elif curr_formula[0].f[0] == self.NOT and curr_formula[1] == 1 and \
                        curr_formula[0].f[1].f[0] == self.VARIABLE: # It's a negated literal!
                    id_str = "%s~%s" % (self.LITERAL_STR, curr_formula[0].f[1].f[1])
                    literals = set([(int(curr_formula[0].f[1].f[1]), False)])
                elif curr_formula[1] < len(curr_formula[0].f): # Explore another element of this non-literal clause!
                    stack.append([curr_formula[0].f[curr_formula[1]], 1])
                    curr_formula[1] += 1
                else: # It's a full logical op! And we've ID'd all the subformulae!
                    op = curr_formula[0].f[0]
                    if op == self.NOT:
                        id_str = self.NOT_STR
                    elif op == self.AND:
                        id_str = self.AND_STR
                    elif op == self.OR:
                        id_str = self.OR_STR

                    f_sub = curr_formula[0].f[1:]
                    f_sub.sort()
                    f_sub_unique = [f_sub[0]]
                    for i in range(1, len(f_sub)):
                        if f_sub[i] != f_sub_unique[-1]:
                            f_sub_unique.append(f_sub[i])
                    for f_sub_id in f_sub_unique:
                        id_str += ",%s" % f_sub_id

                    all_literals = True
                    for f_sub_id in f_sub_unique:
                        if f_sub_id in self.intermediate_nodes or len(self.literal_sets[f_sub_id]) > 1:
                            all_literals = False
                            break
                    if not all_literals:
                        node_is_literal_set = False
                        edges = f_sub_unique
                    else:
                        for f_sub_id in f_sub_unique:
                            lit = self.literal_sets[f_sub_id].pop()
                            if len(self.literal_sets[f_sub_id]) > 0:
                                print("JUSTUS IS CONFUSED! HELP HIM WITH LITERALS!")
                            self.literal_sets[f_sub_id].add(lit)
                            literals.add(lit)

                if id_str is not None: # If the node has been fully identified
                    if len(stack) == 1: # If the node is an output
                        id_str = "%s%s:%s" % (self.OUTPUT_STR, output, id_str)

                    if id_str in self.str_ids_to_num_ids:
                        node_id = self.str_ids_to_num_ids[id_str]
                    else:
                        node_id = self.next_node_id
                        self.str_ids_to_num_ids[id_str] = node_id
                        if node_is_literal_set:
                            print("Node %d is a literal set" % node_id)
                            if len(stack) == 1:
                                self.add_output(output, op, literal_set = literals)
                            else:
                                self.add_literals(literals, op)
                        elif len(stack) == 1: # We're at the base node -- it's an output!
                            self.add_output(output, op, children=edges)
                        else:
                            self.add_intermediate(op, children=edges)

                    stack.pop()
                    if len(stack) > 0:
                        stack[-1][0].f[stack[-1][1] - 1] = node_id

        print("Literal nodes:")
        print({n: (self.ops[n]) for n in self.literal_nodes})
        print("Intermediate nodes:")
        print({n: (self.ops[n]) for n in self.intermediate_nodes})
        print("Output nodes:")
        print({n: (self.ops[n]) for n in self.output_nodes})
        for node in self.all_nodes:
            if node in self.literal_sets:
                print("Node: %d -- Literals: %s" % (node, self.literal_sets[node]))
        print(self.edges)
        """
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

B = BooleanFormula()
B.init_from_string("(x1 || ~x1) || x1")
res2 = BooleanFormulaeOverlapped(res)
"""
