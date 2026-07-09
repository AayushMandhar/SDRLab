"""
Channel impairment simulation module for SDRLab.
Applies multipath fading, Carrier Frequency Offset (CFO), Phase Noise, and AWGN.
"""

import numpy as np
from typing import List, Tuple
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


class NoiseChannel:
    """
    Simulates a physical transmission medium by adding impairments:
    - Multipath fading (tapped-delay line)
    - Carrier Frequency Offset (CFO)
    - Phase Noise (random walk phase variation)
    - Additive White Gaussian Noise (AWGN) based on Eb/N0
    """

    def __init__(
        self,
        cfo_hz: float = 0.0,
        phase_noise_var: float = 0.0,
        multipath_taps: List[float] = None,
        sample_rate: int = 1000000,
    ) -> None:
        """
        Initializes the channel model.
        
        Args:
            cfo_hz: Carrier frequency offset in Hz.
            phase_noise_var: Variance of the phase noise random walk step.
            multipath_taps: List of filter coefficients representing multipath delay profile.
            sample_rate: Sample rate in Hz.
        """
        self.cfo_hz = cfo_hz
        self.phase_noise_var = phase_noise_var
        self.multipath_taps = np.array(multipath_taps if multipath_taps is not set else [1.0], dtype=complex)
        # Normalize multipath taps to conserve power on average
        self.multipath_taps /= np.sqrt(np.sum(np.abs(self.multipath_taps) ** 2))
        self.sample_rate = sample_rate
        
        logger.debug(
            f"NoiseChannel initialized: CFO={cfo_hz} Hz, Phase Noise Var={phase_noise_var}, "
            f"Multipath Taps={self.multipath_taps.tolist()}"
        )

    def apply_multipath(self, signal: np.ndarray) -> np.ndarray:
        """Applies multipath fading using a linear FIR filter (tapped delay line)."""
        if len(self.multipath_taps) == 1 and self.multipath_taps[0] == 1.0:
            return signal
        # Use mode='full' then truncate to keep length aligned
        faded = np.convolve(signal, self.multipath_taps, mode="full")
        return faded[: len(signal)]

    def apply_cfo(self, signal: np.ndarray) -> np.ndarray:
        """Applies Carrier Frequency Offset rotation over time."""
        if self.cfo_hz == 0.0:
            return signal
        t = np.arange(len(signal)) / float(self.sample_rate)
        rotation = np.exp(1j * 2 * np.pi * self.cfo_hz * t)
        return signal * rotation

    def apply_phase_noise(self, signal: np.ndarray) -> np.ndarray:
        """Applies phase noise modeled as a cumulative random walk."""
        if self.phase_noise_var == 0.0:
            return signal
        # Phase noise random walk: theta[n] = theta[n-1] + N(0, phase_noise_var)
        phase_steps = np.random.normal(0, np.sqrt(self.phase_noise_var), size=len(signal))
        phase = np.cumsum(phase_steps)
        rotation = np.exp(1j * phase)
        return signal * rotation

    def add_awgn(self, signal: np.ndarray, eb_n0_db: float, bits_per_symbol: int, sps: int) -> Tuple[np.ndarray, float, float]:
        """
        Adds Additive White Gaussian Noise based on Eb/N0.
        
        Args:
            signal: The input complex sample stream.
            eb_n0_db: Energy per Bit to Noise power spectral density ratio in dB.
            bits_per_symbol: Number of bits per symbol (e.g. 1 for BPSK, 2 for QPSK).
            sps: Samples per symbol.
            
        Returns:
            Tuple[np.ndarray, float, float]:
                - Signal with added noise
                - Measured signal power (Watts)
                - Added noise power (Watts)
        """
        # Measure input signal power
        signal_power = np.mean(np.abs(signal) ** 2)
        
        # Calculate required noise power (sigma^2) based on Eb/N0.
        # Eb/N0 to Es/N0:
        es_n0_db = eb_n0_db + 10 * np.log10(bits_per_symbol)
        # Es/N0 to SNR_sample:
        snr_db = es_n0_db - 10 * np.log10(sps)
        snr_linear = 10 ** (snr_db / 10.0)
        
        # Noise power
        noise_power = signal_power / snr_linear
        
        # Complex noise: real and imaginary parts have variance = noise_power / 2
        noise_std = np.sqrt(noise_power / 2.0)
        noise = noise_std * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
        
        noisy_signal = signal + noise
        logger.debug(
            f"AWGN Added: Eb/N0={eb_n0_db:.2f}dB (SNR_sample={snr_db:.2f}dB). "
            f"Signal Power={signal_power:.4f}W, Noise Power={noise_power:.4f}W."
        )
        return noisy_signal, float(signal_power), float(noise_power)

    def propagate(
        self, signal: np.ndarray, eb_n0_db: float, bits_per_symbol: int, sps: int
    ) -> Tuple[np.ndarray, float, float]:
        """
        Applies all channel impairments in order: Multipath -> CFO -> Phase Noise -> AWGN.
        """
        x = self.apply_multipath(signal)
        x = self.apply_cfo(x)
        x = self.apply_phase_noise(x)
        noisy_x, sig_pwr, noise_pwr = self.add_awgn(x, eb_n0_db, bits_per_symbol, sps)
        return noisy_x, sig_pwr, noise_pwr
