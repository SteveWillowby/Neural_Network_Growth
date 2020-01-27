from network_dag import *
from network_to_formulae import *
from formulae_to_network import *

import readyfunctions
xt, yt, xv, yv = readyfunctions.initMNIST()

GEN_NETWORK = False
TEST_GEN_NETWORK = False

SAVE_NETWORK = False
SAVE_NETWORK_NAME = "saved_5_nn.py"

LOAD_SAVED_NETWORK = False
LOAD_NETWORK_NAME = "saved_5_nn"

SAVE_FORMULAE_NAME = "saved_5_nn_formulae.txt"
LOAD_FORMULAE_NAME = "saved_5_nn_formulae.txt"

if GEN_NETWORK:
    readyfunctions.gen_nn('test__nn.py', maxlayers=2, minlayers=2, \
        maxNodesPerLayer=80, minNodesPerLayer=80) #See the script for the parameters that can be changed

newModule = None
if TEST_GEN_NETWORK:
    import test__nn
    module = test__nn.test__nn()
    newModule, accuracy, output_threshold = readyfunctions.test_nn(module,xt,yt,xv,yv, epochs=500, lr=1.0, loss="CE")
    print("Final Accuracy is: %s" % accuracy)

    weights, biases = readyfunctions.get_weights(newModule)
    connections = newModule.get_connections()
    inputs = newModule.get_inputs()
    outputs = newModule.get_outputs()

if SAVE_NETWORK:
    readyfunctions.create_nn_file([i for i in range(0, 784)], [784 + len(weights) - 10 + i for i in range(0, 10)], \
        connections, weights=weights, biases=biases, filename=SAVE_NETWORK_NAME)

if LOAD_SAVED_NETWORK:
    exec("import %s" % LOAD_NETWORK_NAME)
    exec("module = %s.%s()" % (LOAD_NETWORK_NAME, LOAD_NETWORK_NAME))
    print("Running loaded network for 1 epoch with lr=0.0 just to see performance:")
    newModule, accuracy, output_threshold = readyfunctions.test_nn(module,xt,yt,xv,yv, epochs=0, lr=0.0, loss="CE")
    print("Accuracy is: %s" % accuracy)
    weights, biases = readyfunctions.get_weights(newModule)
    connections = newModule.get_connections()
    inputs = newModule.get_inputs()
    outputs = newModule.get_outputs()

if newModule is not None:
    first_network = NetworkDAG()
    first_network.init_from_trained_module(weights, biases, connections, inputs, outputs)

    print("Built network class representation.")
    print("\nBegin conversion to formulae...")

    # Note! These are shallow formulae!
    print("output threshold is %.3f" % output_threshold)
    formulae = network_to_formulae(first_network, output_threshold)

    print("writing boolean functions to file.")
    readyfunctions.write_formulae_to_file(SAVE_FORMULAE_NAME, formulae)

print("reading simplified boolean functions from file.")
formulae = readyfunctions.read_formulae_from_file(LOAD_FORMULAE_NAME)

#for output, formula in formulae.items():
#    print("Final formula for %s" % output)
#    print(formula.to_string())

print("Beginning to construct overlapped representation.")
new_network, output_order_dict = formulae_to_network(formulae, var_thresh=1.0)
# Note that `formulae` is now destroyed.

new_weights, new_biases, new_connections, new_input_nodes_list, new_output_nodes_list = new_network.convert_to_module(output_order_dict)

readyfunctions.create_nn_file(new_input_nodes_list, new_output_nodes_list, \
    new_connections, weights=new_weights, biases=new_biases, filename="from_bool.py")

import from_bool
module = from_bool.from_bool()
newModule, accuracy, output_threshold = readyfunctions.test_nn(module,xt,yt,xv,yv, epochs=10, lr=1.0, loss="CE")

print("Very last accuracy: %f" % accuracy.item())

print("Conversion finished.")
