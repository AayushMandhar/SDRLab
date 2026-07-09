"""
Unit tests for SDRLab DSP modules (modulator.py, utils.py, transmitter.py, channel.py, receiver.py).
Verifies mapping math, filter normalization, and channel impairments correctness.
"""

import unittest
import numpy as np
from sdrlab.dsp.modulator import ModulatorFactory, BPSKModulator, QPSKModulator
from sdrlab.dsp.utils import rrc_filter
from sdrlab.dsp.transmitter import Transmitter
from sdrlab.dsp.channel import NoiseChannel
from sdrlab.dsp.receiver import Receiver


class TestModulators(unittest.TestCase):
    """Verifies constellation mapping and demapping accuracy for BPSK and QPSK."""

    def test_bpsk_modulator(self) -> None:
        mod = ModulatorFactory.get_modulator("BPSK")
        self.assertEqual(mod.name, "BPSK")
        self.assertEqual(mod.bits_per_symbol, 1)
        
        # Bits map test
        bits = np.array([0, 1, 0, 1, 1, 0])
        expected = np.array([1.0, -1.0, 1.0, -1.0, -1.0, 1.0]) + 0j
        symbols = mod.map_bits_to_symbols(bits)
        np.testing.assert_array_almost_equal(symbols, expected)
        
        # Demap test
        recovered_bits = mod.demap_symbols_to_bits(symbols)
        np.testing.assert_array_equal(recovered_bits, bits)

    def test_qpsk_modulator(self) -> None:
        mod = ModulatorFactory.get_modulator("QPSK")
        self.assertEqual(mod.name, "QPSK")
        self.assertEqual(mod.bits_per_symbol, 2)
        
        # Bits map test (Gray coded)
        # 00 -> 1+1j / sqrt(2)
        # 01 -> 1-1j / sqrt(2)
        # 10 -> -1+1j / sqrt(2)
        # 11 -> -1-1j / sqrt(2)
        bits = np.array([0, 0, 0, 1, 1, 0, 1, 1])
        expected = np.array([1+1j, 1-1j, -1+1j, -1-1j]) / np.sqrt(2.0)
        symbols = mod.map_bits_to_symbols(bits)
        np.testing.assert_array_almost_equal(symbols, expected)
        
        # Demap test
        recovered_bits = mod.demap_symbols_to_bits(symbols)
        np.testing.assert_array_equal(recovered_bits, bits)


class TestDSPUtilities(unittest.TestCase):
    """Verifies filter design functions."""

    def test_rrc_filter_normalization(self) -> None:
        sps = 4
        span = 8
        alpha = 0.35
        
        coeffs = rrc_filter(sps, span, alpha)
        
        # Length check: span * sps + 1
        self.assertEqual(len(coeffs), span * sps + 1)
        
        # Energy normalization check: sum of squares == 1.0
        energy = np.sum(coeffs ** 2)
        self.assertAlmostEqual(energy, 1.0, places=9)
        
        # Symmetry check
        np.testing.assert_array_almost_equal(coeffs, coeffs[::-1])


class TestTransmitterReceiverPipeline(unittest.TestCase):
    """Verifies that an error-free channel loop recovers bits perfectly."""

    def test_end_to_end_back_to_back(self) -> None:
        # Configuration
        mod_type = "QPSK"
        sps = 4
        span = 8
        excess_bw = 0.35
        num_bits = 100
        
        # Modulator bits mapping adjusts to boundary
        tx = Transmitter(mod_type, sps, span, excess_bw)
        bits = tx.generate_random_bits(num_bits)
        
        # Transmit
        tx_waveform, tx_symbols = tx.transmit(bits)
        
        # Perfect, noise-free, offset-free, flat fading channel propagation
        channel = NoiseChannel(cfo_hz=0.0, phase_noise_var=0.0, multipath_taps=[1.0])
        noisy_waveform, _, _ = channel.propagate(
            tx_waveform,
            eb_n0_db=50.0,  # Extremely high SNR to eliminate noise errors
            bits_per_symbol=tx.modulator.bits_per_symbol,
            sps=sps
        )
        
        # Receive (Matched filtering + downsampling)
        rx = Receiver(mod_type, sps, span, excess_bw)
        expected_symbols_count = len(tx_symbols)
        rx_bits, rx_symbols = rx.receive(noisy_waveform, expected_symbols_count)
        
        # Assertions
        # 1. Check dimensions
        self.assertEqual(len(rx_symbols), expected_symbols_count)
        self.assertEqual(len(rx_bits), len(bits))
        
        # 2. Check recovered symbols are close to ideal symbols (decimal=1 to allow minor RRC truncation ISI)
        np.testing.assert_array_almost_equal(rx_symbols, tx_symbols, decimal=1)
        
        # 3. Check error-free bit recovery
        np.testing.assert_array_equal(rx_bits, bits)


if __name__ == "__main__":
    unittest.main()
