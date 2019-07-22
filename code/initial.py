import numpy as np
import networkx as nx
import random
import utility as uti
from collections import defaultdict
from docplex.mp.constants import ComparisonType
from docplex.mp.model import Model
import math
import matplotlib.pyplot as plt

# ------------------------
#       Parameteres      -
# ------------------------
d_replace = 2
network_size = 50

#-------------------------------------------------
#              EXAMPLE RANDOM GRAPHS             -
#-------------------------------------------------
g1 = uti.construct_random_graph("barabasi_c", n = network_size)

max_iter = nx.diameter(g1)


# ------------------------------------------------------------
#             CONSTRUCT THE GROUND TRUTH MAPPING             -
# ------------------------------------------------------------
g1_node_list = np.asarray(g1.nodes()) # list of node ids, starts from 0
g2_node_list = np.random.permutation(g1_node_list) # random permutation of the list of node id

# Construct the ground truth mapping
gt_mapping = dict()
for i in range(len(g1_node_list)):
        gt_mapping[g1_node_list[i]] = g2_node_list[i]

# Construct the ground truth inverse mapping
gt_inverse_mapping = dict()
for i in range(len(g2_node_list)):
    gt_inverse_mapping[g2_node_list[i]] = g1_node_list[i]

# Construct the second graph by relabeling the first graph
g2 = nx.relabel_nodes(g1, gt_mapping)

# ------------------------------------
#         Adjacency matrices         -
# ------------------------------------
C = nx.to_numpy_matrix(g1, dtype = np.int64)
D = nx.to_numpy_matrix(g2, g1_node_list, dtype = np.int64)

for i in range(len(g2)):
    for j in range(len(g2)):
        if D[i, j] == 0:
            D[i, j] = d_replace

# The size of two networks will be differnt for real networks
g1_size = g2_size = network_size

# ------------------------------ 
#   Initial Similarity Matrix  -
# ------------------------------
S = np.ones((g1_size, g2_size), np.float64)

# ------------------------------
#     Initial Greedy Vector    -
# ------------------------------
b = np.ones(((g1_size + g2_size), 1), np.float64)

#-------------------------Iteration will starts here --------------------------#

for _ in range(max_iter):
	# ------------------------
	#       new S and b      -
	# ------------------------
	b_new = np.ones(((g1_size + g2_size), 1), np.float64)
	b_new = np.negative(b_new)
	
	S_new = np.zeros((g1_size, g2_size), np.float64) # the only time we use S_new is assignment, therefore, its initial value doesn't matter

	# NOTE: for b and b_new, the index of u is u + g1_size
	for i in g1.nodes():
		for u in g2.nodes():
			# ---------------------------------------
			#    The complete bipartite graph       -
			# ---------------------------------------
			# Instead of constructing the actural graph (which is costly), we create a dictionary B with the format:
			# {(j, v) : [weight, 0]}
			# the 0 means this edge has not been deleted
			B = defaultdict(lambda : [0.0, 0])
			for j in g1.neighbors(i):
				for v in g2.neighbors(u):
					B[(j, v)][0] = S[j, v]

			# format (list of tuples): [ ( (j, v), [weight, 0] ) ]
			sorted_B = uti.special_sort_dict(B)

			c = 0 # accumulated similarity values
			num_deleted_edges = 0
			index_of_the_largest_undeleted_edge = 0

			while num_deleted_edges != len(sorted_B):
				while sorted_B[index_of_the_largest_undeleted_edge][1][1]:
					index_of_the_largest_undeleted_edge += 1
				# format: ((j, v), [weight, 0])
				largest = sorted_B[index_of_the_largest_undeleted_edge]
				j = largest[0][0]
				v = largest[0][1]
				weight = largest[1][0]
				if weight == b[j,0] and weight == b[v + g1_size, 0]: # perfect matching
					c += weight
					for edge in sorted_B:
						if (j == edge[0][0] or v == edge[0][1]) and edge[1][1] == 0:
							num_deleted_edges += 1
							edge[1][1] = 1
				elif weight == b[j,0] and weight < b[v + g1_size, 0]: # half matching
					c += 2 * weight - b[v + g1_size, 0]
					for edge in sorted_B:
						if (j == edge[0][0] or v == edge[0][1]) and edge[1][1] == 0:
							num_deleted_edges += 1
							edge[1][1] = 1
				elif weight < b[j,0] and weight == b[v + g1_size, 0]: # half matching
					c += 2 * weight - b[j, 0]
					for edge in sorted_B:
						if (j == edge[0][0] or v == edge[0][1]) and edge[1][1] == 0:
							num_deleted_edges += 1
							edge[1][1] = 1
				elif weight < b[j,0] and weight < b[v + g1_size, 0]: # no matching
					sorted_B[index_of_the_largest_undeleted_edge][1][1] = 1
					num_deleted_edges += 1
				
			maxi = max(len(list(g1.neighbors(i))), len(list(g2.neighbors(u))))
			S_new[i,u] = c / maxi
			if S_new[i,u] > b_new[i]:
				b_new[i] = S_new[i,u]
			if S_new[i,u] > b_new[u + g1_size]:
				b_new[u + g1_size] = S_new[i,u]
	# Update
	b = b_new
	S = S_new

mapping = dict()
selected = [0] * (g2_size)

for i in range(S.shape[0]):
	maxi = -1
	max_index = 0
	for u in range(S.shape[1]):
		if S[i,u] > maxi and not selected[u]:
			maxi = S[i, u]
			max_index = u 
	mapping[i] = max_index
	selected[max_index] = 1

matched_node = 0
for i in range(S.shape[0]):
    if gt_mapping[i] == mapping[i]: 
        matched_node += 1
print("Initial mapping percentage: {}".format(matched_node / S.shape[0]))

count = 0
for i1 in range(len(g1)):
	for j1 in range(len(g1)):
		i2 = mapping[i1]
		j2 = mapping[j1]
		if C[i1, j1] == 1:
			if D[i2, j2] == d_replace:
				count += 1
		if C[i1, j1] == 0:
			if D[i2, j2] == 1:
				count += 1
print("Initial violations: {}".format(count))

# Archive
# g1 = nx.read_edgelist("test1.edgelist", nodetype = int)
# g2 = nx.read_edgelist("test2.edgelist", nodetype = int)

# g1_node_list = list(g1.nodes()) 
# g2_node_list = list(g2.nodes())

# gt_mapping = {0 : 0, 1 : 1, 2 : 2, 3 : 3, 4 : 4, 5 : 5, 6 : 6, 7 : 7, 8 : 8}