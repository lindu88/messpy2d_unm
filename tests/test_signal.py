from Instruments.signal_processing import first, fast_stats, fast_stats2d, fast_signal, fast_signal2d
import numpy as np
from numpy.testing import assert_almost_equal

import pytest

@pytest.fixture
def array():
    np.random.seed(1)
    x = 100+10*np.random.random((128, 10000))
    return x

def test_first():
    arr = np.zeros(10000)
    arr[5] = 3
    assert(first(arr, 1) == 5)
    arr[5000] = 50
    assert (first(arr, 4) == 5000)


def classic1d(x):
    mean, std, mi, ma = x.mean(),  x.std(), x.min(), x.max()
    return mean, std, mi, ma


def test_classic_stats(array, benchmark):
    benchmark(classic1d, array[:, 0])


def test_fast_stats(array, benchmark):
    x = array[0, :]
    mean, std, mi, ma = benchmark(fast_stats, x)
    assert_almost_equal(x.mean(), mean)
    assert_almost_equal(x.std(), std)
    assert_almost_equal(x.min(), mi)
    assert_almost_equal(x.max(), ma)


def classic(x):
    mean, std, mi, ma = x.mean(1),  x.std(1), x.min(1), x.max(1)
    return mean, std, mi, ma


def test_classic_stats2d(array, benchmark):
    benchmark(classic, array)


def test_fast_stats2d(array, benchmark):
    a = benchmark(fast_stats2d, array)
    b = classic(array)
    assert_almost_equal(b[0], a[:, 0])
    assert_almost_equal(b[1], a[:, 1])
    assert_almost_equal(b[2], a[:, 2])
    assert_almost_equal(b[3], a[:, 3])


def classic_signal(a):
    return np.log10(a[::2].mean() / a[1::2].mean()) * 1000


def classic_signal2d(a):
    return np.log10(a[:, ::2].mean() / a[::-1, 1::2].mean()) * 1000


def test_classic_signal(array, benchmark):
    a = array[0, :]
    benchmark(classic_signal, a)

def test_classic_signal2d(array, benchmark):
    benchmark(classic_signal2d, array)

def test_fast_signal(array, benchmark):
    a = array[0, :]
    mOD = classic_signal(a)
    mOD_fast = benchmark(fast_signal, a)
    assert_almost_equal(mOD_fast, mOD, 3)


def test_fast_signal2d(array, benchmark):
    benchmark(fast_signal2d, array)
