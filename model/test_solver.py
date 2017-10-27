import solver as sv
import random
import sys
import numpy as np

def printnow(s):
	sys.stdout.write(s)
	sys.stdout.flush()

def main(argv):
	random.seed(1)
	np.random.seed(1)
	m = 3       # samples
	n = 4       # leaves
	l = 6       # breakpoints
	r = 10      # segments
	c_max = 7  # maximum copy number
	f_scale = 5

	U = gen_U(m, n)
	Q = np.array([ np.arange(0, r) == random.randint(0, r-1) for bp in xrange(l) ], dtype = int)
	F = gen_F(Q, m, l, r, f_scale)
	G = gen_G(l)
	A = np.random.binomial(100, 0.25, [m, l])
	H = 100 * np.ones([m, l])
	lamb1 = 1
	lamb2 = 0.01

	test_get_U(F, n, l, r)
	test_get_C(F, Q, G, A, H, n, c_max, lamb1, lamb2)
	test_get_UCE(F, Q, G, A, H, n, c_max, lamb1, lamb2, max_iters = 2)

# mixed copy number
def gen_F(Q, m, l, r, f_scale):
	h_scale = float(f_scale) / 2.0 # scale for breakpoints
	F = h_scale * np.random.rand(m, l + r)
	for b in xrange(0, l):
		for s in xrange(0, r):
			if Q[b, s] == 1:
				for p in xrange(0, m):
					F[p, l+s] = max(F[p, l+s], F[p, b])
					F[p, l+s] += h_scale * np.random.rand()
	return F

# mated pair binary matrix
def gen_G(l):
	G = np.zeros((l, l))
	I = [ x for x in xrange(0, l) ]   # list of all indicies
	random.shuffle(I)                 # randomly permut to make random pairs
	I = np.array(I).reshape((l/2, 2)) # make a l/2 by 2 numpy array of mated pairs
	for i, j in I:
		G[i, j] = 1
		G[j, i] = 1
		G[i, i] = 1
		G[j, j] = 1
	return G

def gen_C(n, l, r):
	C = np.random.rand(2*n-1, l+r)
	C = (C * 4).round()
	C[2*n-2, :l] = 0
	C[2*n-2, l:] = 2
	return C

# generate random U matrix
def gen_U(m, n):
	U = np.random.rand(m, 2*n-1)
	rowsums = np.sum(U, 1)
	for i in xrange(m):
		U[i, :] = U[i, :] / rowsums[i]
	return U

# # # # # # # # #
#   T E S T S   #
# # # # # # # # #

def test_get_UCE(F, Q, G, A, H, n, c_max, lamb1, lamb2, max_iters = 5):
	printnow('\ntest_get_UCE starting\n')
	U, C, E, obj_val, err_msg = sv.get_UCE(F, Q, G, A, H, n, c_max, lamb1, lamb2, max_iters)

	if err_msg != None:
		printnow(err_msg + '\n')
	else:
		printnow(str(U) + '\n')
		printnow(str(C) + '\n')
		printnow(str(E) + '\n')
		printnow('objective value is ' + str(obj_val) + '\n')

	printnow('\ntest_get_UCE complete\n')

def test_get_U(F, n, l, r):
	N = 2*n-1
	C = gen_C(n, l, r)
	printnow('\ntest_get_U starting\n')
	U = sv.get_U(F, C, n)
	printnow(str(U) + '\n')
	printnow('test_get_U complete\n')

def test_get_C(F, Q, G, A, H, n, c_max, lamb1, lamb2):
	m = len(F)
	U = gen_U(m, n)
	printnow('\ntest_get_C starting\n')
	obj_val, C, E, R, err_msg = sv.get_C(F, U, Q, G, A, H, n, c_max, lamb1, lamb2)

	if err_msg != None:
		printnow(err_msg + '\n')
	else:
		printnow(str(C) + '\n')
		printnow(str(E) + '\n')
		printnow('objective value is ' + str(obj_val) + '\n')

	printnow('test_get_C complete\n')

#
#   CALL TO MAIN
#


if __name__ == "__main__":
	main(sys.argv[1:])
