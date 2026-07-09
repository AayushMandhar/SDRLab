"""
Receiver module for SDRLab.
Performs matched filtering, timing synchronization, and demodulates complex symbols back to bits.
"""

import numpy as np
from typing import Tuple
from sdrlab.dsp.modulator import ModulatorFactory
from sdrlab.dsp.utils import rrc_filter
from sdrlab.dsp.synchronization import BaseTimingSynchronizer, BaseCarrierSynchronizer, IdealTimingSynchronizer, IdealCarrierSynchronizer
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


class Receiver:
    """
    Simulates the receiver baseband processing:
    - Applies matched RRC filtering.
    - Uses symbol timing synchronization to sample at optimal peak.
    - Applies carrier synchronization (pass-through in V1, ready for PLLs).
    - Demaps symbols to binary bits.
    """

    def __init__(
        self,
        modulation_type: str,
        sps: int,
        filter_span: int,
        excess_bw: float,
        timing_sync: BaseTimingSynchronizer = None,
        carrier_sync: BaseCarrierSynchronizer = None,
    ) -> None:
        """
        Initializes the receiver.
        
        Args:
            modulation_type: The modulation scheme (e.g., 'BPSK', 'QPSK').
            sps: Samples per symbol.
            filter_span: RRC filter span in symbols.
            excess_bw: RRC excess bandwidth (roll-off factor).
            timing_sync: Optional timing synchronizer instance. If None, uses IdealTimingSynchronizer.
            carrier_sync: Optional carrier synchronizer instance. If None, uses IdealCarrierSynchronizer.
        """
        self.modulator = ModulatorFactory.get_modulator(modulation_type)
        self.sps = sps
        self.filter_span = filter_span
        self.excess_bw = excess_bw
        
        # Design matched RRC filter
        self.rrc_coeffs = rrc_filter(self.sps, self.filter_span, self.excess_bw)
        
        # Set timing recovery (default to IdealTimingSynchronizer using total group delay: transmitter delay + receiver delay)
        # Tx filter adds (span * sps / 2) samples of delay in 'full' convolution mode.
        # Rx filter adds (span * sps / 2) samples of delay in 'full' convolution mode.
        # Total delay to peak is exactly (span * sps) samples.
        total_filter_delay = self.filter_span * self.sps
        self.timing_sync = timing_sync if timing_sync is not None else IdealTimingSynchronizer(total_filter_delay)
        
        # Set carrier tracking (default to IdealCarrierSynchronizer)
        self.carrier_sync = carrier_sync if carrier_sync is not None else IdealCarrierSynchronizer()
        
        logger.debug(
            f"Receiver initialized with {modulation_type}. Timing Sync: {type(self.timing_sync).__name__}, "
            f"Carrier Sync: {type(self.carrier_sync).__name__}"
        )

    def receive(self, noisy_waveform: np.ndarray, expected_sym_count: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Processes received noisy baseband samples to recover transmitted bits.
        
        Args:
            noisy_waveform: 1D complex array of received channel samples.
            expected_sym_count: The number of symbols expected to be received (used to truncate trailing transients).
            
        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - Decoded binary bits (1D array of 0s and 1s)
                - Extracted complex symbols (post timing/carrier sync, at symbol rate)
        """
        # 1. Matched Filter (convolving noisy signal with local RRC coefficients)
        matched_filtered = np.convolve(noisy_waveform, self.rrc_coeffs, mode="full")
        
        # 2. Timing Synchronization (Downsample at peak eye-openings)
        symbols_sampled = self.timing_sync.synchronize(matched_filtered, self.sps)
        
        # Truncate to expected number of symbols to discard tail transients
        if len(symbols_sampled) > expected_sym_count:
            symbols_sampled = symbols_sampled[:expected_sym_count]
        elif len(symbols_sampled) < expected_sym_count:
            # Handle edge cases where signal was clipped, pad with zero symbols
            logger.warning(
                f"Receiver recovered fewer symbols ({len(symbols_sampled)}) than expected ({expected_sym_count}). Padding with zeros."
            )
            padding = np.zeros(expected_sym_count - len(symbols_sampled), dtype=complex)
            symbols_sampled = np.concatenate([symbols_sampled, padding])
            
        # 3. Carrier Synchronization (compensating phase and CFO)
        symbols_corrected = self.carrier_sync.synchronize(symbols_sampled)
        
        # 4. Demap Symbols to Bits
        rx_bits = self.modulator.demap_symbols_to_bits(symbols_corrected)
        
        logger.info(
            f"Received: {len(noisy_waveform)} samples -> {len(symbols_corrected)} symbols -> {len(rx_bits)} bits."
        )
        return rx_bits, symbols_corrected
