#!/usr/bin/env python
# coding: utf-8

import math
from boolean_formula import *

# In[ ]:

#Downloads MNIST and sets up train and validate sets

def initMNIST():
    from pathlib import Path
    import requests
    import pickle
    import gzip
    import torch

    DATA_PATH = Path("data")
    PATH = DATA_PATH / "mnist"

    PATH.mkdir(parents=True, exist_ok=True)

    URL = "http://deeplearning.net/data/mnist/"
    FILENAME = "mnist.pkl.gz"

    if not (PATH / FILENAME).exists():
        content = requests.get(URL + FILENAME).content
        (PATH / FILENAME).open("wb").write(content)



    with gzip.open((PATH / FILENAME).as_posix(), "rb") as f:
        ((x_train, y_train), (x_valid, y_valid), _) = pickle.load(f, encoding="latin-1")

    # Convert y_train and y_valid to 1-hot encoding format.
    y_train = [[float(int(y == x)) for x in range(0,10)] for y in y_train]
    y_valid = [[float(int(y == x)) for x in range(0,10)] for y in y_valid]

    x_train, y_train, x_valid, y_valid = map(
        torch.tensor, (x_train, y_train, x_valid, y_valid)
    )
    return x_train, y_train, x_valid, y_valid


# In[2]:


#-------------------------------------
# This function generates a file for a pytorch nn
# The number of hidden layers, nodes per hidden
#   layer, and connections between layers are random
#
# filename. The filename of the new file, will be 
#   'randmodule' + str(randint(1000,1000000)) by default
#
# maxlayers. Max possible number of random hidden layers.
#   Default is 1
#
# minlayers. Min possible number of random hidden layers.
#   Default is 1
#
# maxNodesPerLayer. Max possible number of nodes per hidden
#   layer. Default is 1.
# minNodesPerLayer. Min possible number of nodes per hidden
#   layer. Default is 1.
#
# inputsize/outputsize. Not used for this project.
#--------------------------------------


def gen_nn(filename="userandom",
           maxlayers=1, minlayers=1,
           maxNodesPerLayer=1, minNodesPerLayer=1,
           inputsize=784,outputsize=10):
    #------------imports------------------------------------
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from random import randint
    from random import sample

    #------------decide filename if none given--------------
    if filename == "userandom":
        filename = "randmodule"+str(randint(1000,1000000))
        
    if filename[-3]=='.':
        modname=filename[:-3]
    else:
        modname=filename

    #------------decide number of layers--------------------
    laynum = randint(minlayers,maxlayers)

    TYPICAL_INPUT_DEGREE = 5

    #------------decide nodes per layer---------------------
    TOTIN=inputsize
    TOTOUT=outputsize
    nodesByLayer = [TOTIN]

    while nodesByLayer[-1] > TOTOUT:
        layer_size = 2 * int(nodesByLayer[-1] / TYPICAL_INPUT_DEGREE)
        layer_size = max(layer_size, TOTOUT)
        nodesByLayer.append(layer_size)
    laynum = len(nodesByLayer) - 2
    print("Using %d hidden layers with an average of %d inputs per neuron" % (laynum, TYPICAL_INPUT_DEGREE))

    #for i in range(0,laynum):
    #    nodesByLayer.append(randint(minNodesPerLayer,maxNodesPerLayer))
    #nodesByLayer.append(TOTOUT)

    #------------make a variable name for each node---------
    layer_vars = []
    for li, nodes in enumerate(nodesByLayer):
        t = []
        for ni in range(0,nodes):
            t.append("lin"+str(li)+"_"+str(ni))
        layer_vars.append(t)

    #------------init multi-dim lists in python-------------
    input_sets = []
    for i in range(0,laynum+2):
        input_sets_t = []
        for j in range(0,nodesByLayer[i]):
            input_sets_t.append(set())
        input_sets.append(input_sets_t)

    for i in range(0,TOTIN):
        t = sample(range(0,nodesByLayer[1]), 1) #min(nodesByLayer[1], randint(1,AVERAGE_OUTPUT_DEGREE)))
        for node in t:
            input_sets[1][node].add(i)
    for i in range(0,nodesByLayer[1]):
        already_has = len(input_sets[1][i])
        t = sample(range(0,nodesByLayer[0]), min(nodesByLayer[0], max(1, TYPICAL_INPUT_DEGREE - already_has))) #randint(1,AVERAGE_OUTPUT_DEGREE)))
        for node in t:
            if layer_vars[0][node] not in input_sets[1][i]:
                input_sets[1][i].add(node)

    #------------do the rest of the layers-----------------
    for j in range(1,laynum+1):
        for i in range(0,nodesByLayer[j]):
            t = sample(range(0,nodesByLayer[j+1]), 1) #min(nodesByLayer[j+1], randint(1,AVERAGE_OUTPUT_DEGREE)))
            for node in t:
                input_sets[j+1][node].add(i)
        for i in range(0,nodesByLayer[j+1]):
            already_has = len(input_sets[j+1][i])
            t = sample(range(0,nodesByLayer[j]), min(nodesByLayer[j], max(1, TYPICAL_INPUT_DEGREE - already_has))) #randint(1,AVERAGE_OUTPUT_DEGREE)))
            for node in t:
                if layer_vars[j][node] not in input_sets[j+1][i]:
                    input_sets[j+1][i].add(node)

    input_ids_in_order = [i for i in range(0, 784)]
    layer_id_start = 784
    prev_layer_id_start = 0
    node_input_lists = {}
    for layer in input_sets[1:]:
        for input_list_id in range(0, len(layer)):
            node_input_lists[input_list_id + layer_id_start] = sorted([prev_layer_id_start + i for i in layer[input_list_id]])
        prev_layer_id_start = layer_id_start
        layer_id_start += len(layer)
    output_ids_in_order = [(layer_id_start - 10) + i for i in range(0, 10)]
    create_nn_file(input_ids_in_order, output_ids_in_order, node_input_lists, filename=filename)


# In[ ]:


def get_weights(module):
    weights = {}
    biases = {}
    for node in module.get_nodes():
        weights[node] = module._modules["node_"+str(node)].weight[0].tolist()
        biases[node] = module._modules["node_"+str(node)].bias.item()
    return weights, biases


# In[ ]:


#-------------------------------------
# This function tests a nn
#
# module. The pytorch nn to test
#
# x_train,y_train,x_valid,y_valid. whatever
#
#lr. learning rate
#
#epochs. The number of epochs
#
#bs. Batch size
#--------------------------------------
def test_nn(module, x_train, y_train, x_valid, y_valid, lr=0.01, epochs=2, bs=64, loss="MSE"):
    import torch.nn.functional as F
    from torch.utils.data import TensorDataset
    from torch.utils.data import DataLoader
    from torch import optim
    import torch

    if loss == "CE":
        loss_func = torch.nn.CrossEntropyLoss()
        y_train = torch.argmax(y_train, dim=1)
    if loss == "BCE":
        loss_func = torch.nn.BCELoss()
    if loss == "MSE":
        loss_func = torch.nn.MSELoss()
    if loss == "L1":
        loss_func = torch.nn.L1Loss()

    train_ds = TensorDataset(x_train, y_train)
    train_dl = DataLoader(train_ds, batch_size=bs)

    model= module 
    opt = optim.SGD(model.parameters(), lr=lr)

    for epoch in range(epochs):
        print("epoch :",epoch)
        i=0
        for xb, yb in train_dl:
            i=i+1
            if i%100==0:
                print(i)
                print(loss.item())
            pred = model(xb)

            loss = loss_func(pred, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()

    pred = model(x_valid)
    #print(pred[0])
    #print(torch.argmax(pred[0]))
    preds = torch.argmax(pred, dim=1)
    #print(preds)
    y_valid = torch.argmax(y_valid, dim=1)
    #print(y_valid)
    acc = (preds == y_valid).float().mean()

    # This next code is due to the fact that CE loss uses a sigmoid, so final outputs are not driven to 1/0.
    max_v = 0
    second_max_v = 0
    for val in pred[0]:
        if max_v < val:
            second_max_v = max_v
            max_v = val
        elif second_max_v < val:
            second_max_v = val
    output_threshold = (max_v + second_max_v) / 2.0
    actual_output_threshold = math.log(output_threshold / (1.0 - output_threshold), 2.4)
    return model, acc, actual_output_threshold


# weights and biases, if provided, should be dictionaries. weights leads to lists in sorted order
def create_nn_file(input_ids_in_order, output_ids_in_order, node_input_lists, weights=None, biases=None, filename="convertedNN.py"):
    if filename[-3:]=='.py':
        modname = filename[:-3]
    else:
        modname = filename

    num_inputs_str = str(len(input_ids_in_order))

    with open(filename,'w') as f:
        f.write("import torch\n")
        f.write("import torch.nn as nn\n")
        f.write("from random import randint\n\n")
        f.write("class "+modname+"(nn.Module):\n")
        f.write("\tdef __init__(self):\n")

        #The Layers
        f.write("\t\tsuper().__init__()\n")

        sorted_node_names = [node for node, il in node_input_lists.items()]
        sorted_node_names.sort()
        for node in sorted_node_names:
            input_list = node_input_lists[node]
            s = "\t\tself.node_"+str(node)+" = nn.Linear("+str(len(input_list))+",1)\n"
            f.write(s)
            if weights is not None:
                s = "\t\tself.node_"+str(node)+".weight = torch.nn.Parameter(torch.tensor("+str([weights[node]])+"))\n"
                f.write(s)
            if biases is not None:
                s = "\t\tself.node_"+str(node)+".bias = torch.nn.Parameter(torch.tensor("+str([biases[node]])+"))\n"
                f.write(s)

        #the forward process
        f.write("\tdef forward(self,x):\n")

        s = "\n\t\tinputs = torch.split(x, split_size_or_sections="+num_inputs_str+")"
        f.write(s)
        s = "\n\t\txt = torch.t(x)"
        f.write(s)

        for idx in range(0, len(input_ids_in_order)):
            s = "\n\t\toutput_"+str(input_ids_in_order[idx])+" = xt["+str(idx)+"]"
            f.write(s)

        for node in sorted_node_names:
            input_list = node_input_lists[node]
            node = str(node)
            if len(input_list) > 1:
                s = "\n\t\tinput_"+node+" = torch.t(torch.stack(("
                s += str(["torch.squeeze(output_"+str(val)+")" for val in list(input_list)])[1:-1].replace("'","")
                s += ")))\n"
            else:
                print("HAD A NODE WITH ONLY ONE INPUT! ERROR! WE DONT KNOW HOW TO HANDLE THIS YET!")
                raise ValueError("Oh dear.")
                s = "\n\t\tinput_"+node+" = torch.squeeze(output_" + str(input_list[0]) + ")\n"
            f.write(s)
            s = "\n\t\toutput_"+node+" = torch.sigmoid(self.node_"+node+"(input_"+node+"))"
            f.write(s)

        s = "\n\t\treturn torch.cat(" + str(["output_"+str(output_id) for output_id in output_ids_in_order]).replace("'","") + ", axis=1)"
        f.write(s)

        f.write("\n\tdef get_nodes(self):\n")
        f.write("\t\treturn "+str(sorted([node for node, input_set in node_input_lists.items()])))

        f.write("\n\tdef get_inputs(self):\n")
        f.write("\t\treturn "+str(input_ids_in_order))

        f.write("\n\tdef get_outputs(self):\n")
        f.write("\t\treturn "+str(output_ids_in_order))

        #return the connections
        f.write("\n\tdef get_connections(self):\n")
        dict_str = ""
        for node, input_list in node_input_lists.items():
            dict_str += str(node)+": "+str(input_list)+","
        dict_str = dict_str[:-1] # Remove final comma.
        f.write("\t\treturn {"+dict_str+"}")
        f.close()

# In[ ]:


#-------------------------------------
# Sets the weights for a torch nn
#
# module = the nn to change
#
# weights = a dict mapping a node to a list of weights
#
# biases = a dict mapping a node to a bias
#
# All numbers passed in must be float
#--------------------------------------
def manualSetWeights(module,weights=None,biases=None):
    if weights is not None:
        for node, weights_list in weights:
            module._modules["node_"+str(node)].weight = torch.nn.Parameter(torch.tensor([weights_list]))
    if biases is not None:
        for node, bias in biases:
            module._modules["node_"+str(node)].bias = torch.nn.Parameter(torch.tensor([bias]))

def write_formulae_to_file(filename, formulae):
    with open(filename,'w') as f:
        keys = [output for output, form in formulae.items()]
        keys.sort()
        for key in keys:
            f.write(formulae[key].to_string())
            f.write("\n")
        f.close()

def read_formulae_from_file(filename):
    with open(filename,'r') as f:
        formulae = {}
        bool_strs = f.readlines()
        for i in range(0, len(bool_strs)):
            B = BooleanFormula()
            B.init_from_string(bool_strs[i][:-1], shallow=True)
            formulae[i] = B
            print("Read formula %d / %d" % (i+1, len(bool_strs)))
        f.close()
        return formulae
