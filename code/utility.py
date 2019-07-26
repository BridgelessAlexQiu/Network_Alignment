import networkx as nx
import numpy as np
import operator
import random
from docplex.mp.constants import ComparisonType
from docplex.mp.model import Model

#----------------------------degree seqeunce------------------------------------
# Return the degree sequence, format (dict): {node1: degree, node2: degree, ...}
def degree_sequence(G):
    sequence = dict()
    for node, degree in G.degree():
        sequence[node] = degree
    return sequence

#--------------------------Check if a matrix is symmetric----------------------
def is_symmetric(a, rtol=1e-05, atol=1e-08):
    return np.allclose(a, a.T, rtol=rtol, atol=atol)

#--------------------------Sort dictionary----------------------------------
def sort_dict(d : "the dictionary", dec = True):
    if dec:
        sorted_d = sorted(d.items(), key=lambda kv: kv[1], reverse = True)
    else:
        sorted_d = sorted(d.items(), key=lambda kv: kv[1])
    return sorted_d

#--------------------------Sort dictionary----------------------------------
def special_sort_dict(d : "the dictionary", dec = True):
    if dec:
        sorted_d = sorted(d.items(), key=lambda kv: kv[1][0], reverse = True)
    else:
        sorted_d = sorted(d.items(), key=lambda kv: kv[1][0])
    return sorted_d

#---------------------------random graph generator--------------------------
# Return a particular random graph
def construct_random_graph(type = "barabasi_c", n = 300, p = 40, m = 0.4):
    if type == "barabasi_c":
        return nx.powerlaw_cluster_graph(n, p, m)
    elif type == "barabasi":
        return nx.barabasi_albert_graph(n, p)
    elif type == "erdos":
        return nx.fast_gnp_random_graph(n, 0.3)
    else:
        raise ValueError('Unknown graph type!')

#-----------------------------Oppostive identity operation---------------------
def Oi(I):
    one = np.ones((I.shape[0], I.shape[0]), np.int64)
    return (one - I)


#-----------------------------Initial permuation matrix---------------------------

# Construct the initial similarity matrix
def initial_solution(g1, g2, node_list, r : "the perturbation probability", n):
    dim = (len(g1), len(g2)) # dimeonsion of the permutation matrix
    pi = np.zeros(dim, np.int64) # the permutation matrix, initial entries are 0

    # Sort nodes by degrees in descending order. format : list of tuples with size 2
    sorted_ds_g1 = sorted(g1.degree(), key=operator.itemgetter(1), reverse=True)
    sorted_ds_g2 = sorted(g2.degree(), key=operator.itemgetter(1), reverse=True)

    # Adjacency matrix of two networks
    A1 = nx.to_numpy_matrix(g1, dtype = np.int64)
    A2 = nx.to_numpy_matrix(g2, node_list, dtype = np.int64) # the rows and columns are ordered according to the nodes in g1

    # Initial solution, the while loop is necessary here because we want to skip w.s.p
    i = 0
    while i < len(g1):
        # vertices with ith degree ranking in two graphs
        u1 = int(sorted_ds_g1[i][0])
        u2 = int(sorted_ds_g2[i][0])

        # Modified Big-Align Approach
        rand = random.uniform(0, 1)
        if rand >= r or i == n-1:
            pi[u1, u2] = 1
        else:
            i += 1
            v1 = int(sorted_ds_g1[i][0])
            v2 = int(sorted_ds_g2[i][0])
            pi[u1, v2] = 1
            pi[v1, u2] = 1

        i += 1
    return pi


#-------------------------------Refinement by swapping pairs (baseline)-------------------------
def pairwise_refine(g1, g1_node_list, pi, mapping, C, D, objective, max_iter = 300):
    for z in range(max_iter):
    # random sample 30 nodes from the graph
        V_1 = []
        for _ in range(30):
            rand = random.uniform(0, len(g1))
            V_1.append(g1_node_list[int(rand)])

        for i1 in range(len(V_1)-1):
            u1 = V_1[i1]
            # we don't include vertices in V_1 in the neighborhood
            n1 = set(g1.neighbors(u1))
            n1 = list(n1 - set(V_1))
            for j1 in range(i1 + 1):
                v1 = V_1[j1]
                u2 = mapping[u1]
                v2 = mapping[v1]
                old_part_1 = C[u1, v1] * D[u2, v2]
                new_part_1 = C[u1, v1] * D[v2, u2]

                new_part_2 = 0
                for n in n1:
                    new_part_2 += C[u1, n] * D[v2, mapping[n]]
                old_part_2 = 0
                for n in n1:
                    old_part_2 += C[u1, n] * D[u2, mapping[n]]

                n2 = set(g1.neighbors(v1))
                n2 = list(n2 - set(V_1))

                new_part_3 = 0
                for n in n2:
                    new_part_3 += C[v1, n] * D[u2, mapping[n]]
                old_part_3 = 0
                for n in n2:
                    old_part_3 += C[v1, n] * D[v2, mapping[n]]

                if (new_part_1 + new_part_2 + new_part_3) < (old_part_1 + old_part_2 + old_part_3):
                    objective = objective - (old_part_1 + old_part_2 + old_part_3) + (new_part_1 + new_part_2 + new_part_3)
                    mapping[u1] = v2
                    mapping[v1] = u2
                    pi[u1, u2] = 0
                    pi[u1, v2] = 1
                    pi[v1, v2] = 0
                    pi[v1, u2] = 1
    return mapping, pi

#------------------------------------------- Ising function-------------------------------------------

def solve_ising(B, bias):
    """
    Ising model: \sum_{i,j} H_ij \pi_i \pi_j + \sum_i J_i \pi_i
    """
    mdl = Model()
     # note that B is the sub-matrix
    n = B.shape[0]

    # dict of bianry decision variables, format: {i : bdv_i}
    x = {i: mdl.binary_var(name='x_{0}'.format(i)) for i in range(n)}

    # objective function
    # (2 * x[i] - 1) * (2 * x[j] - 1): s_i \in {-1,+1}
    couplers_func =  mdl.sum(B[i,j] * x[i] * x[j] for i in range(n) for j in range(n)) # s_i \in {0,1}
    bias_func = mdl.sum(float(bias[i]) * x[i] for i in range(n))
    ising_func = couplers_func + bias_func

    mdl.minimize(ising_func)
    solution = mdl.solve()
    cplex_solution = solution.get_all_values()

    # print('CPLEX solution: ', [int(1-2*i) for i in cplex_solution])  s_i \in {-1,+1}
    # print('CPLEX solution: ', cplex_solution)
    return cplex_solution

# ------------------ IsoRank -----------------------#
def IsoRank(A1, A2, tol = 0.000005, max_iter = 500, H = None):
	# Shapes of two matrices
	n1 = A1.shape[0]
	n2 = A2.shape[0]

	# Normalization of adjacency matrix
	row_sum_1 = np.zeros((n1, 1), np.float64)
	row_sum_2 = np.zeros((n2, 1), np.float64)

	for i in range(n1):
		row_sum_1[i, 0] = 1/np.sum(A1[i])
		row_sum_2[i, 0] = 1/np.sum(A2[i])

	W1 = np.multiply(row_sum_1, A1)
	W2 = np.multiply(row_sum_2, A2)

	# Inilization of similarity matrix
	S = np.full((n2, n1), 1/(n1 * n2))

	# Prior similarity matrix
	if not H:
		H = S

	# Main iterations
	for i in range(max_iter):
		prev = S
		W2_t = np.transpose(W2)
		M1 = np.matmul(W2_t, S)
		M2 = np.matmul(M1, W1)
		S = 0.5 * M2 + 0.5 * H
		delta = np.linalg.norm(S - prev)
		if delta < tol:
			print("Total number of iterations: {}".format(i))
			break
		print("One itration complete")

	return S