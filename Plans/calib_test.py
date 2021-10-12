import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

x, y2o, y1o = np.load('calib.npy').T

y1 = gaussian_filter1d(y1o, 1)
y2 = gaussian_filter1d(y2o, 1)
fig, (ax0, ax1) = plt.subplots(2)
ax0.plot(x, y1o, alpha=0.3, lw=0.4, c='C0')
ax0.plot(x, y2o, alpha=0.3, lw=0.4, c='C0')

ax0.plot(x, y1)
ax0.plot(x, y2)
p, pd = find_peaks(y1, distance=10, prominence=1000)
ax0.plot(x[p], y1[p], 'o', ms=10)
p2, pd2 = find_peaks(y2, prominence=1000, distance=10)
ax0.plot(x[p2], y2[p2], 'o', ms=10)
single = 6000
width = 150
dist = 500 - width
a = np.arange(0, 4096*3, 500)



align = np.argmin(abs(x[p]-x[p2]))
pix0 = 6000+width/2
print(align)
pixel = a[:len(p)]-a[align]+pix0
from scipy.constants import c
freqs = c/x[p]/1e3
freq0 = c/x[p2]/1e3

ax1.plot(pix0, freq0, marker='o', ms=10)
ax0.set_xlabel('Wavelength / nm')
ax1.set_xlabel('Pixel')
ax1.set_ylabel('Freq / THz')

ax1.plot(pixel, freqs, marker='x', ms=10)
p = np.polyfit(pixel, freqs, 2)
fit = np.polyval(p, pixel)
txt = ''.join(['%.3e\n'%i for i in p])
ax1.annotate(txt, (0.95, 0.93), xycoords='axes fraction', va='top', ha='right' )
ax1.plot(pixel, fit, color='k')
fig.tight_layout()
plt.show()
