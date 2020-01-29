from boolean_formulae import *
from quine_mccluskey.qm import QuineMcCluskey

qm = QuineMcCluskey(use_xor=False)
result = qm.simplify([2, 1], [])
print(result)

result = qm.simplify([4, 5, 2, 1], [])
print(result)

# Check out https://users.ece.utexas.edu/~patt/06s.382N/tutorial/espresso_manual.html

# The QM solver takes a list of integers, which state that:
# if the bits exactly match that integer, the function returns solvable.
# The second array contains "don't care" bits, which means that that assignemnt can be ignored (??).

# The output is essentially a DNF formula. Where zeros represent negated vars, 1's represent vars, and
#     -'s represent that the var is not in the clause.

def get_total_num_vars(bf, variables=set()):
    pass

def get_satisfying_assignments(bf, total_num_vars, var_ids={}, next_var_id=0):
    assignments_for_bf = []

    return next_var_id
