from Instruments.signal_processing import first, fast_stats, fast_stats2d, fast_signal, fast_signal2d
import numpy as np
from numpy.testing import assert_almost_equal


def test_first():
    arr = np.zeros(10000)
    arr[5] = 3
    assert(first(arr, 1) == 5)
    arr[5000] = 50
    assert (first(arr, 4) == 5000)


def test_faststats():
    np.random.seed(1)
    x = np.random.random(10000)
    mean, std, mi, ma = fast_stats(x)
    assert_almost_equal(x.mean(), mean)
    assert_almost_equal(x.std(), std)
    assert_almost_equal(x.min(), mi)
    assert_almost_equal(x.max(), ma)


def test_faststats2d():
    np.random.seed(1)
    x = np.random.random((100, 10000))
    a = fast_stats2d(x)
    assert_almost_equal(x.mean(1), a[:, 0])
    assert_almost_equal(x.std(1), a[:, 1])
    assert_almost_equal(x.min(1), a[:, 2])
    assert_almost_equal(x.max(1), a[:, 3])


def test_fastsignal():
    np.random.seed(1)
    x = np.random.random((100, 10000))
    a = x[0, :]
    mOD = np.log10(a[::2].mean()/a[1::2].mean())*1000
    print(fast_signal(a), mOD)
