"""
DSP utility functions for SDRLab.
Includes filter design functions such as Root Raised Cosine (RRC) coefficient generators.
"""

import numpy as np


def rrc_filter(sps: int, span: int, alpha: float) -> np.ndarray:
    """
    Generates coefficients for a Root Raised Cosine (RRC) filter.
    
    Args:
        sps: Samples per symbol.
        span: Filter span in symbols (half-length is span * sps).
        alpha: Excess bandwidth (roll-off factor), between 0 and 1.
        
    Returns:
        np.ndarray: Normalised filter coefficients.
    """
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError("Alpha (roll-off) must be between 0.0 and 1.0.")
    if sps <= 1:
        raise ValueError("sps must be > 1.")
    if span <= 0:
        raise ValueError("span must be > 0.")

    # Number of taps
    num_taps = span * sps + 1
    t = np.arange(num_taps) - (num_taps - 1) / 2.0
    
    # Avoid division by zero by adding a small offset to t for specific conditions
    # We will compute the response carefully
    h = np.zeros(num_taps)
    
    for i, t_val in enumerate(t):
        # Scale to symbol period Ts = 1.0, so sample period is Ts/sps = 1/sps
        t_normalized = t_val / float(sps)
        
        if t_normalized == 0.0:
            h[i] = 1.0 - alpha + 4.0 * alpha / np.pi
        elif alpha != 0.0 and abs(abs(t_normalized) - 1.0 / (4.0 * alpha)) < 1e-9:
            # Singular point at t = +- Ts / (4 * alpha)
            h[i] = (alpha / np.sqrt(2.0)) * (
                (1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * alpha))
                + (1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * alpha))
            )
        else:
            numerator = np.sin(np.pi * t_normalized * (1.0 - alpha)) + 4.0 * alpha * t_normalized * np.cos(np.pi * t_normalized * (1.0 + alpha))
            denominator = np.pi * t_normalized * (1.0 - (4.0 * alpha * t_normalized) ** 2)
            h[i] = numerator / denominator
            
    # Normalize filter energy to unity (gain of 1 at symbol rate)
    h /= np.sqrt(np.sum(h ** 2))
    return h
