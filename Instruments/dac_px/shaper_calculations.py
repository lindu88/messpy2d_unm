from scipy.constants import c
import numpy as np


def THz2cm(nu):
    return (nu * 1e10) / c


def cm2THz(nu):
    return c / (nu * 1e10)


def double_pulse_mask(
    nu: np.ndarray, nu_rf: float, tau: float, phi1: float, phi2: float
):
    """
    Return the mask to generate a double pulse

    Parameters
    ----------
    nu : array
        freqs of the shaper pixels in THz
    nu_rf : float
        rotating frame freq of the scanned pulse in THz
    tau : float
        Interpulse distance in ps
    phi1 : float
        Phase shift of the scanned pulse
    phi2 : float
        Phase shift of the fixed pulse
    """
    double = 0.5 * (
        np.exp(-1j * (nu - nu_rf) * 2 * np.pi * tau) * np.exp(+1j * phi1)
        + np.exp(1j * phi2)
    )
    return double


def delay_scan_mask(nu: np.ndarray, tau: np.ndarray, phi: np.ndarray):
    """
    Generate masks to different time delays.
    """
    return np.exp(-1j * nu * 2 * np.pi * tau) * np.exp(+1j * phi)


def dispersion(nu, nu0, GVD, TOD, FOD):
    x = nu - nu0
    x *= 2 * np.pi
    facs = np.array([GVD, TOD, FOD]) / np.array([2, 6, 24])
    return x ** 2 * facs[0] + x ** 3 * facs[1] + x ** 3 * facs[2]
