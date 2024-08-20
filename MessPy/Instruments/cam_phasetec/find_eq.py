# %%
import numpy as np
import matplotlib.pyplot as plt

rows = 128
colums = 128
a = np.arange(128 * 128)

bi = np.swapaxes(a.reshape(rows // 4, colums, 4), 0, 1).reshape(rows, colums)
# %%

av = a.reshape(128, 128)
# %%
t = np.zeros_like(av)
for r in range(128):
    for c in range(128):
        k = (c % 4) * 512 // 128
#            t[r, c] = a[i + k + r*128]

for i in range(a.size):
    r = i // 128
    c = i % 128
    k = (c // 4) * (4 * 128) + c % 4 + r * 4
    t.flat[i] = a[k]
    print(r, c, av[r, c], bi[r, c], k, k - bi[r, c])


i = np.arange(128 * 128)
k = ((i % 128) // 4) * 512 + i % 4 + i // 128 * 4


# %%
n = np.arange(128 * 128)
a[(n % 512)].reshape(128, 128)[:10, :10]
# %%

import zipfile

np.savez("bla2", a=a)

# %%
f = np.load("bla.npz")
f["a"]


# %%
import io
bio = io.BytesIO()
np.save(bio, bi)
# %%
bio
bio.getbuffer().tobytes()# %%

# %%

with zipfile.ZipFile("bla2.npz", "a") as z:
    z.writestr("b.npy", data=bio.getbuffer().tobytes())
# %%
with zipfile.ZipFile("bla2.npz", "r") as z:
    print(z.filelist)
# %%
np.load("bla2.npz")["b"]
# %%


#include <cstdint>
#include <stdio.h>

#include <stdint.h>

int sum_given_rows(uint16_t two_d_input[128][128], uint32_t two_d_output[][128], 
                    int n_givens, int *lower, int *upper, int rowsize) {
    // Iterate through each given row range
    for (int i = 0; i < n_givens; i++) {
        int lower_bound = lower[i];
        int upper_bound = upper[i];

        // Check bounds validity
        if (lower_bound < 0 || upper_bound < 0 || lower_bound >= upper_bound || upper_bound >= rowsize) {
            // Invalid bounds
            return 1; // Skip invalid range
        }

        // Calculate the sum for the current row range
        
        for (int k = 0; k < 128; k++) {
            two_d_output[i][k] = 0;
            for (int j = lower_bound; j <= upper_bound; j++) {
                two_d_output[i][k] += two_d_input[j][k];
        }
        }

        
    }
    return 0;
}
