# Interface for Network class:
#    get_input_nodes()
#    get_output_nodes()
#    get_hidden_nodes()
#    get_biases()

#    get_edges()
#    get_edges_with_weights()

#    get_children(name)
#    get_children_with_weights(name)

#    get_parents(name)
#    get_parents_with_weights(name)

#    add_input(name)
#    add_output(name)
#    add_hidden(name)
#    delete_node(name)

#    add_edge(parent, child, weight, check_no_cycle=True)
#    delete_edge(parent, child)

#    topological_sort_order(top_to_bottom=False)

class NetworkDAG:

    def __init__(self):
        self.input_nodes = set()
        self.output_nodes = set()
        self.hidden_nodes = set()
        self.all_nodes = set()
        self.biases = {}
        self.edges = {}
        self.children = {}
        self.parents = {}

    def init_from_trained_module(self, weights, biases, connections, inputs, outputs):
        self.__init__()
        for i in inputs:
            self.add_input(i)
        if len(weights) != len(connections):
            print("Un-equal lengths! :( %d, %d" % (len(weights), len(connections)))
        for node, connection_list in connections.items():
            if node in outputs:
                self.add_output(node, biases[node])
            else:
                self.add_hidden(node, biases[node])

            for connection_idx in range(0, len(connection_list)):
                if len(weights[node]) != len(connections[node]):
                    print("%d VS %d (at layer node %d)" % (len(weights[node]), len(connections[node]), node))
                input_node = connection_list[connection_idx]
                weight = weights[node][connection_idx]
                self.add_edge(input_node, node, weight, check_no_cycle=False)

    # Before converting to a module, this makes sure to rename the nodes so that they are in the proper order.
    def convert_to_module(self, output_order_dict):
        input_nodes_list = list(self.input_nodes)
        input_nodes_list.sort()
        output_nodes_list = list(self.output_nodes)
        output_nodes_list = [(output_order_dict[node], node) for node in output_nodes_list]
        output_nodes_list.sort()
        output_nodes_list = [x[1] for x in output_nodes_list]

        topological_order = self.topological_sort_order(top_to_bottom=True)

        hidden_nodes_list = []
        for t_node in topological_order:
            if t_node in self.hidden_nodes:
                hidden_nodes_list.append(t_node)

        # Ensure each node has at least 2 inputs by adding connections with weight 0.
        for node in hidden_nodes_list + output_nodes_list:
            np = 0
            while len(self.parents[node]) < 2:
                while topological_order[np] in self.parents[node]:
                    np += 1
                self.add_edge(topological_order[np], node, 0.0)
                print("Needed to add a connection for node %d to get its num of inputs up to >= 2." % node)
                np += 1

        next_node_id = 0
        id_substitutions = {}
        for node in input_nodes_list:
            id_substitutions[node] = next_node_id
            next_node_id += 1

        for node in hidden_nodes_list:
            id_substitutions[node] = next_node_id
            next_node_id += 1

        for node in output_nodes_list:
            id_substitutions[node] = next_node_id
            next_node_id += 1

        weights = {id_substitutions[node]: [x[1] for x in sorted([(id_substitutions[p], w) for p, w in self.parents[node].items()])]\
            for node in output_nodes_list + hidden_nodes_list}
        connections = {id_substitutions[node]: [x[0] for x in sorted([(id_substitutions[p], w) for p, w in self.parents[node].items()])]\
            for node in output_nodes_list + hidden_nodes_list}
        biases = {id_substitutions[node]: bias for node, bias in self.biases.items()}
        input_nodes_list = [id_substitutions[node] for node in input_nodes_list]
        output_nodes_list = [id_substitutions[node] for node in output_nodes_list]

        return weights, biases, connections, input_nodes_list, output_nodes_list

    def get_input_nodes(self):
        return set(self.input_nodes)
    def get_output_nodes(self):
        return set(self.output_nodes)
    def get_hidden_nodes(self):
        return set(self.hidden_nodes)

    # Returns the set of all edges in the network: (parent, child, weight)
    def get_edges(self):
        return set([e for e, w in self.edges.items()])

    def get_edges_with_weights(self):
        return set([(p, c, w) for (p, c), w in self.edges.items()])

    def get_biases(self):
        return dict(self.biases)

    def get_children(self, name):
        if name not in self.all_nodes:
            raise ValueError("ERROR: node %s not in network (call to get_children())" % name)
        return set([c for c, w in self.children[name].items()])

    def get_children_with_weights(self, name):
        if name not in self.all_nodes:
            raise ValueError("ERROR: node %s not in network (call to get_children_with_weights())" % name)
        return set([(c, w) for c, w in self.children[name].items()])

    def get_parents(self, name):
        if name not in self.all_nodes:
            raise ValueError("ERROR: node %s not in network (call to get_parents())" % name)
        return set([p for p, w in self.parents[name].items()])

    def get_parents_with_weights(self, name):
        if name not in self.all_nodes:
            raise ValueError("ERROR: node %s not in network (call to get_parents_with_weights())" % name)
        return set([(p, w) for p, w in self.parents[name].items()])

    def add_input(self, name):
        if name in self.all_nodes:
            raise ValueError("ERROR: node %s already in network (call to add_input())" % name)
        self.input_nodes.add(name)
        self.all_nodes.add(name)
        self.parents[name] = {}
        self.children[name] = {}

    def add_output(self, name, bias):
        if name in self.all_nodes:
            raise ValueError("ERROR: node %s already in network (call to add_output())" % name)
        self.output_nodes.add(name)
        self.all_nodes.add(name)
        self.parents[name] = {}
        self.children[name] = {}
        self.biases[name] = bias

    def add_hidden(self, name, bias):
        if name in self.all_nodes:
            raise ValueError("ERROR: node %s already in network call to add_hidden())" % name)
        self.hidden_nodes.add(name)
        self.all_nodes.add(name)
        self.parents[name] = {}
        self.children[name] = {}
        self.biases[name] = bias

    def delete_node(self, name):
        if name not in self.all_nodes:
            raise ValueError("ERROR: node %s not in the network" % name)
        for c, w in self.children[name].items():
            del self.edges[(name, c)]
            del self.parents[c][name]
        for p, w in self.parents[name].items():
            del self.edges[(p, name)]
            del self.children[p][name]
        del self.children[name]
        del self.parents[name]

        self.all_nodes.remove(name)
        if name in self.input_nodes:
            self.input_nodes.remove(name)
        elif name in self.output_nodes:
            self.output_nodes.remove(name)
            del self.biases[name]
        else:
            self.hidden_nodes.remove(name)
            del self.biases[name]

    def add_edge(self, parent, child, weight, check_no_cycle=True):
        if parent not in self.all_nodes:
            raise ValueError("ERROR: node %s not in network" % parent)
        if child not in self.all_nodes:
            raise ValueError("ERROR: node %s not in network" % child)
        if child in self.children[parent]:
            raise ValueError("ERROR: edge (%s, %s) already exists" % (parent, child))
        if child == parent:
            raise ValueError("ERROR: cannot create an edge from a node to itself (%s, %s)" % (parent, child))
        if child in self.input_nodes:
            raise ValueError("ERROR: cannot create an edge pointing to an input (%s, %s)" % (parent, child))
        if parent in self.output_nodes:
            raise ValueError("ERROR: cannot create an edge coming from an output node (%s, %s)" % (parent, child))
        if check_no_cycle:
            if self.a_ancestor_b(child, parent):
                raise ValueError("ERROR: attempted to create a cycle by adding edge (%s, %s)" % (parent, child))
        self.edges[(parent, child)] = weight
        self.children[parent][child] = weight
        self.parents[child][parent] = weight

    def a_ancestor_b(self, a, b):
        the_stack = [a]
        while len(the_stack) > 0:
            node = the_stack.pop()
            if node == b:
                return True
            for c, w in self.children[node].items():
                the_stack.append(c)
        return False

    # For some reason this was failing.
    def topological_sort_order_old(self, top_to_bottom=False):
        sortable_nodes = [TopoSortHelperClass(name, self) for name in self.all_nodes]
        sortable_nodes.sort(reverse=top_to_bottom)
        return [tshc.n for tshc in sortable_nodes]

    # Unfortunatly, this will be a simple insertion sort until something better may be contrived.
    def topological_sort_order(self, top_to_bottom=False):
        all_nodes_list = list(self.all_nodes)
        final_order = []
        all_nodes_len = len(all_nodes_list)
        for i in range(0, all_nodes_len):
            min_node = all_nodes_list[0]
            min_node_idx = 0
            for j in range(1, len(all_nodes_list)):
                if top_to_bottom and self.a_ancestor_b(all_nodes_list[j], min_node):
                    min_node_idx = j
                    min_node = all_nodes_list[j]
                elif (not top_to_bottom) and self.a_ancestor_b(min_node, all_nodes_list[j]):
                    min_node_idx = j
                    min_node = all_nodes_list[j]
            final_order.append(min_node)
            all_nodes_list[min_node_idx] = all_nodes_list[-1]
            all_nodes_list.pop()
        return final_order

    def delete_edge(self, parent, child):
        if (parent, child) not in self.edges:
            raise ValueError("ERROR: edge (%s, %s) does not exist" % (parent, child))
        del self.parents[child][parent]
        del self.children[parent][child]
        del self.edges[(parent, child)]

class TopoSortHelperClass:

    def __init__(self, node, networkDAG):
        self.n = node
        self.nDAG = networkDAG

    def __lt__(self, other):
        return self.nDAG.a_ancestor_b(other.n, self.n)

    def __le__(self, other):
        return not self.nDAG.a_ancestor_b(self.n, other.n)

    def __gt__(self, other):
        return self.nDAG.a_ancestor_b(self.n, other.n)

    def __ge__(self, other):
        return not self.nDAG.a_ancestor_b(other.n, self.n)

    def __eq__(self, other):
        return (not self.nDAG.a_ancestor_b(other.n, self.n)) and (not self.nDAG.a_ancestor_b(self.n, other.n))

#N = NetworkDAG()
#N.add_hidden("a", 1)
#N.add_hidden("b", 1)
#N.add_hidden("c", 1)
#N.add_hidden("d", 1)
#N.add_edge("b", "a", 1)
#N.add_edge("c", "b", 1)
#N.add_edge("d", "a", 1)
#N.add_edge("c", "d", 1)
#N.add_edge("b", "d", 1)
#print(N.topological_sort_order())
