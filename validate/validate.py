#     file: validate.py
#   author: Jesse Eaton
#  created: 10/23/2017
# modified: 10/23/2017
#  purpose: reports error in copy number for breakpoints, copy number for segments,
#             usage, and phylogeny topology (using robinson foulds distance) after
#             doing maximal matching between copy number profiles of clones


# # # # # # # # # # #
#   I M P O R T S   #
# # # # # # # # # # #

import sys      # for command line arguments
import os       # for manipulating files and folders
import argparse # for command line arguments
import numpy as np
from sympy.utilities.iterables import multiset_permutations # permuting rows in C

sys.path.insert(0, '../help/')
import file_manager as fm   # sanitizes file and directory arguments
import post_processing as pp


# # # # # # # # # # # # #
#   C O N S T A N T S   #
# # # # # # # # # # # # #

FNAMES = ['C.tsv', 'U.tsv', 'T.dot', 'F.tsv', 'obj_val.txt'] # these files must be in 'actual' and 'expected' dirs. MUST BE IN THIS ORDER


# # # # # # # # # # # # #
#   F U N C T I O N S   #
# # # # # # # # # # # # #

def main(argv):
	args = get_args(argv)
	score_Cb, score_Cs, score_C, score_U, dist_T, score_FUC, obj_val = get_scores(args['actual_directory'], args['expected_directory'])
	
	print ' Cb: ' + str(score_Cb)
	print ' Cs: ' + str(score_Cs)
	print '  C: ' + str(score_C)
	print '  U: ' + str(score_U)
	print '  T: ' + str(dist_T)
	print 'FUC: ' + str(score_FUC)
	print 'obj: ' + str(obj_val)

#  input: act_dir (str) name of directory containing T.dot, C.tsv, and U.tsv estimated by tusv.py
#         exp_dir (str) name of dire...                                  ... generated by sim.py
# output: score_Cb (int) L1 distance between expected and actual copy number of breakpoints
#         score_Cs (int) L1 distance between expected and actual copy number of segments
#         score_C (int) L1 distance between expected and actual copy number matrix
#         score_U (float) L1 distance between expected and actual usage matrix U
#         score_FUC (float) L1 distance between expected and actual mixed copy number F
#         obj_val (float) objective value returned by tusv.py
#         dist (int) Robinson - Foulds distance between expected and actual tree
def get_scores(act_dir, exp_dir):
	Ca, Ua, Ta = pp.get_CUT(act_dir)
	Ce, Ue, Te = pp.get_CUT(exp_dir)
	m, N, l, r = get_mNlr(Ca, Ua)

	F = get_F(act_dir)
	obj_val = get_obj_val(act_dir)

	perm = get_best_perm(Ca, Ce, Ua, Ue, N)

	score_Cb = get_L1_score(Ca[perm, :l], Ce[:, :l])
	score_Cs = get_L1_score(Ca[perm, l:], Ce[:, l:])
	score_C = get_L1_score(Ca[perm, :], Ce)
	if Ua.ndim == 1:
		score_U = get_L1_score(Ua[perm], Ue)
	else:
		score_U = get_L1_score(Ua[:, perm], Ue)

	reorder_nodes(Ta, perm)

	dist_T = Ta.robinson_foulds(Te)[0] # continue here with trying to permute nodes to match better

	# calculate |F - U*C|
	if Ua.ndim == 1:
		score_FUC = np.sum(np.abs(F - np.dot(Ua[perm], Ca[perm, :])))
	else:
		score_FUC = np.sum(np.abs(F - np.dot(Ua[:, perm], Ca[perm, :])))
	
	return score_Cb, score_Cs, score_C, score_U, dist_T, score_FUC, obj_val

def reorder_nodes(T, perm):
	for node in T.traverse():
		node.name = str(perm[int(node.name.split('[')[0])])

def get_best_perm(Ca, Ce, Ua, Ue, N):
	clone_idxs = [ x for x in xrange(0, N) ]
	perms = [ p for p in multiset_permutations(clone_idxs)]
	perms = get_perms_best_C_score(Ca, Ce, perms)
	perm = get_perm_best_U_score(Ua, Ue, perms)
	return perm

def get_perms_best_C_score(Ca, Ce, perms):
	best_perms = []
	best_score = float("inf")
	for perm in perms:
		score = get_L1_score(Ca[perm, :], Ce)
		if score == best_score:
			best_perms.append(perm)
		elif score < best_score:
			best_score = score
			best_perms = [perm]
	return best_perms

def get_perm_best_U_score(Ua, Ue, perms):
	best_perm = perms[0]
	best_score = float("inf")
	for perm in perms:
		if Ua.ndim == 1:
			score = get_L1_score(Ua[perm], Ue)
		else:
			score = get_L1_score(Ua[:, perm], Ue)
		if score < best_score:
			best_score = score
			best_perm = perm
	return perm


#  input: X (np.array)
#         Y (np.array) same dimensions as Y
#   does: removes any columns in X or Y that has any negative values
# output: score (float) L1 distance between X and Y
def get_L1_score(X, Y):
	m, n = X.shape
	cols_to_remove = [ j for j in xrange(0, n) if np.any(X[:, j] < 0) or np.any(Y[:, j] < 0) ]
	X = np.delete(X, cols_to_remove, axis = 1)
	Y = np.delete(Y, cols_to_remove, axis = 1)
	return np.sum(np.absolute(X - Y))

# LAST ROW OF C IS ASSUMED TO BE ROOT NODE
def get_mNlr(C, U):
	N = len(C)
	l = 0
	while C[N-1, l] == 0:
		l += 1
	r = len(C[0, :]) - l
	m = len(U)
	return m, N, l, r

# # # # # # # # # # # # # # # # # # #
#   F I L E S   T O   A R R A Y S   #
# # # # # # # # # # # # # # # # # # #

def get_F(dirname):
	return np.genfromtxt(dirname + FNAMES[3], dtype = float)

def get_obj_val(dirname):
	return np.genfromtxt(dirname + FNAMES[4], dtype = float)
	

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   C O M M A N D   L I N E   A R G U M E N T   F U N C T I O N S   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def get_args(argv):
	parser = argparse.ArgumentParser(prog = 'template.py', description = "purpose")
	parser.add_argument('-a', '--actual_directory', required = True, type = lambda x: fm.valid_dir_with_files(parser, x, FNAMES), help = 'directory containing T.dot, C.tsv, and U.tsv that were estimated by tusv.py')
	parser.add_argument('-e', '--expected_directory', required = True, type = lambda x: fm.valid_dir_with_files(parser, x, FNAMES[:3]), help = 'directory containing different T.dot, C.tsv, and U.tsv files that were generated by sim.py')
	return vars(parser.parse_args(argv))

def is_valid_file(parser, arg):
	if not os.path.exists(arg):
		parser.error('The file \"' + str(arg) + '\" could not be found.')
	else:
		return open(arg, 'r')


# # # # # # # # # # # # # # # # # # # # # # # # #
#   C A L L   T O   M A I N   F U N C T I O N   #
# # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":
	main(sys.argv[1:])
