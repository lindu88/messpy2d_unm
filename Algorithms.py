import numpy as np
from numba import njit, jit
import random
from math import sqrt

@njit
def correlated_noise(n, k):
    out = np.empty(n)
    sigma = 2/sqrt(2*k)
    out[0] = random.normalvariate(0, sigma)*k
    for i in range(1, n):
        out[i] = out[i-1]*(1-k) + k*random.normalvariate(0, sigma)
        print(out[i])
    return out

def signal(t, omega1, tau1, omega2, tau2):
    return 0.001*


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    plt.plot(correlated_noise(4000, 1/60))
    plt.show()