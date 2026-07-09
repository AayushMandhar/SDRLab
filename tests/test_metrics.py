"""
Unit tests for SDRLab Metrics module (metrics.py).
Verifies correctness of empirical and theoretical BER, EVM, and SNR calculations.
"""

import unittest
import numpy as np
from sdrlab.metrics import (
    calculate_empirical_ber,
    calculate_theoretical_ber,
    calculate_evm,
    calculate_snr_db,
)


class TestMetrics(unittest.TestCase):
    """Checks mathematical correctness of SDR communication metrics."""

    def test_empirical_ber(self) -> None:
        tx = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        
        # 0 errors
        rx_perfect = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        self.assertEqual(calculate_empirical_ber(tx, rx_perfect), 0.0)
        
        # 50% errors (4 errors)
        rx_half_errors = np.array([1, 0, 1, 0, 0, 1, 0, 1])
        self.assertEqual(calculate_empirical_ber(tx, rx_half_errors), 0.5)

        # Dimension mismatch handling: should truncate and run
        rx_truncated = np.array([0, 1, 0, 1])  # length 4
        self.assertEqual(calculate_empirical_ber(tx, rx_truncated), 0.0)

    def test_theoretical_ber_bounds(self) -> None:
        # Theoretical BPSK/QPSK BER at 0 dB: 0.5 * erfc(1) = 0.5 * 0.1573 = 0.0786
        ber_0db = calculate_theoretical_ber("BPSK", 0.0)
        self.assertAlmostEqual(ber_0db, 0.0786496, places=5)
        
        # Check QPSK at 0dB (should be same as BPSK)
        qpsk_0db = calculate_theoretical_ber("QPSK", 0.0)
        self.assertEqual(qpsk_0db, ber_0db)

        # BER at higher SNR should be much lower
        ber_10db = calculate_theoretical_ber("BPSK", 10.0)
        self.assertLess(ber_10db, 1e-5)

    def test_error_vector_magnitude(self) -> None:
        tx = np.array([1+0j, -1+0j, 1+0j, -1+0j])
        
        # 0 EVM
        self.assertEqual(calculate_evm(tx, tx), 0.0)
        
        # Adding error vector of magnitude 0.1 to all symbols:
        # RMS error vector magnitude is 0.1, reference magnitude is 1.0, EVM should be 10%
        rx = tx + 0.1 + 0.0j
        self.assertAlmostEqual(calculate_evm(tx, rx), 10.0, places=5)

    def test_snr_decibel_conversion(self) -> None:
        # Signal power 2W, Noise power 0.2W -> ratio = 10 -> 10 dB
        self.assertEqual(calculate_snr_db(2.0, 0.2), 10.0)
        
        # Signal power 1W, Noise power 1W -> ratio = 1 -> 0 dB
        self.assertEqual(calculate_snr_db(1.0, 1.0), 0.0)
        
        # Edge cases
        self.assertEqual(calculate_snr_db(0.0, 1.0), float("-inf"))
        self.assertEqual(calculate_snr_db(1.0, 0.0), float("inf"))


if __name__ == "__main__":
    unittest.main()
