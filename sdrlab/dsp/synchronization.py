"""
Synchronization interfaces and basic implementations.
Defines plugin endpoints for timing recovery and carrier tracking.
"""

from abc import ABC, abstractmethod
import numpy as np


class BaseTimingSynchronizer(ABC):
    """
    Abstract interface for Symbol Timing Synchronization (e.g. Gardner, Early-Late).
    """

    @abstractmethod
    def synchronize(self, signal: np.ndarray, sps: int) -> np.ndarray:
        """
        Processes high-rate samples and extracts symbol-rate samples at optimal eye-opening.
        
        Args:
            signal: 1D complex samples after matched filtering.
            sps: Samples per symbol.
            
        Returns:
            np.ndarray: Complex symbols downsampled to symbol rate.
        """
        pass


class BaseCarrierSynchronizer(ABC):
    """
    Abstract interface for Carrier Recovery (Frequency and Phase tracking loops like Costas Loop).
    """

    @abstractmethod
    def synchronize(self, symbols: np.ndarray) -> np.ndarray:
        """
        Tracks and corrects phase/frequency offsets in symbol-rate complex numbers.
        
        Args:
            symbols: 1D complex symbol-rate samples.
            
        Returns:
            np.ndarray: Phase-corrected symbol-rate samples.
        """
        pass


class IdealTimingSynchronizer(BaseTimingSynchronizer):
    """
    Timing synchronizer that assumes ideal clock alignment and uses a known filter delay.
    For standard RRC pulse-shaping, the filter delay is: span * sps / 2 samples.
    """

    def __init__(self, filter_delay_samples: int) -> None:
        """
        Args:
            filter_delay_samples: Number of samples the signal was delayed due to filter convolution.
        """
        self.delay = filter_delay_samples

    def synchronize(self, signal: np.ndarray, sps: int) -> np.ndarray:
        # Slice off filter startup transients and down-sample starting at optimal symbol peak
        # The peak of the first symbol is at the filter delay index.
        if len(signal) <= self.delay:
            return np.array([], dtype=complex)
        
        # Down-sample at peak points
        symbols = signal[self.delay :: sps]
        return symbols


class IdealCarrierSynchronizer(BaseCarrierSynchronizer):
    """
    Default carrier synchronizer that performs no corrections (pass-through).
    Can be replaced by Costas Loops or Decision-Directed PLLs in future revisions.
    """

    def __init__(self, frequency_offset_hz: float = 0.0, phase_offset_rad: float = 0.0, sample_rate: int = 1000000) -> None:
        self.fo = frequency_offset_hz
        self.po = phase_offset_rad
        self.fs = sample_rate

    def synchronize(self, symbols: np.ndarray) -> np.ndarray:
        # Ideal compensation if parameters are known, otherwise pass-through.
        # V1 defaults to pass-through since impairments are simulated without PLL tracking.
        return symbols
