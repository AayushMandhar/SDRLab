"""
Transmitter module for SDRLab.
Generates bits, maps them to complex symbols, and applies RRC pulse shaping.
"""

import numpy as np
from typing import Tuple
from sdrlab.dsp.modulator import ModulatorFactory
from sdrlab.dsp.utils import rrc_filter
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


class Transmitter:
    """
    Simulates the transmitter frontend:
    - Generates random bit sequences.
    - Modulates bits to complex constellation symbols.
    - Performs pulse shaping using Root Raised Cosine (RRC) filtering.
    """

    def __init__(self, modulation_type: str, sps: int, filter_span: int, excess_bw: float) -> None:
        """
        Initializes the transmitter.
        
        Args:
            modulation_type: The modulation scheme (e.g., 'BPSK', 'QPSK').
            sps: Samples per symbol.
            filter_span: RRC filter span in symbols.
            excess_bw: RRC excess bandwidth (roll-off factor).
        """
        self.modulator = ModulatorFactory.get_modulator(modulation_type)
        self.sps = sps
        self.filter_span = filter_span
        self.excess_bw = excess_bw
        
        # Design RRC filter
        self.rrc_coeffs = rrc_filter(self.sps, self.filter_span, self.excess_bw)
        logger.debug(
            f"Transmitter initialized with {modulation_type}. RRC filter length: {len(self.rrc_coeffs)} taps."
        )

    def generate_random_bits(self, num_bits: int) -> np.ndarray:
        """
        Generates a random sequence of bits (0s and 1s).
        Ensures the bit count is compatible with the modulator bits_per_symbol.
        """
        bps = self.modulator.bits_per_symbol
        remainder = num_bits % bps
        if remainder != 0:
            adjusted_bits = num_bits + (bps - remainder)
            logger.warning(
                f"Adjusting num_bits from {num_bits} to {adjusted_bits} to align with {self.modulator.name} symbol size ({bps} bits)."
            )
            num_bits = adjusted_bits
            
        return np.random.randint(0, 2, size=num_bits)

    def transmit(self, bits: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Processes bits to produce baseband complex samples.
        
        Args:
            bits: 1D array of binary bits.
            
        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - Transmitted baseband complex samples (analog-like filtered waveform)
                - Original complex symbols (pre-filtering, at symbol rate)
        """
        # 1. Modulate
        symbols = self.modulator.map_bits_to_symbols(bits)
        
        # 2. Upsample (insert sps-1 zeros between symbols)
        symbols_upsampled = np.zeros(len(symbols) * self.sps, dtype=complex)
        symbols_upsampled[::self.sps] = symbols
        
        # 3. Pulse shape convolution
        # We use 'full' to capture the filter tails, but record filter delay.
        tx_waveform = np.convolve(symbols_upsampled, self.rrc_coeffs, mode="full")
        
        logger.info(
            f"Transmitted: {len(bits)} bits -> {len(symbols)} symbols -> {len(tx_waveform)} samples."
        )
        return tx_waveform, symbols
