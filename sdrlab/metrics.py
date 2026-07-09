"""
Metrics module for SDRLab.
Computes performance characteristics of communication systems, such as BER, SNR, and EVM.
"""

import numpy as np
from scipy.special import erfc
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


def calculate_empirical_ber(tx_bits: np.ndarray, rx_bits: np.ndarray) -> float:
    """
    Computes the empirical Bit Error Rate (BER).
    
    Args:
        tx_bits: 1D array of transmitted binary bits.
        rx_bits: 1D array of received binary bits.
        
    Returns:
        float: Bit Error Rate (between 0.0 and 1.0).
    """
    if len(tx_bits) != len(rx_bits):
        min_len = min(len(tx_bits), len(rx_bits))
        logger.warning(
            f"Transmitted bits count ({len(tx_bits)}) differs from received ({len(rx_bits)}). "
            f"Truncating to shortest length {min_len} for comparison."
        )
        tx_bits = tx_bits[:min_len]
        rx_bits = rx_bits[:min_len]

    if len(tx_bits) == 0:
        return 0.0

    bit_errors = np.sum(tx_bits != rx_bits)
    ber = float(bit_errors) / len(tx_bits)
    logger.debug(f"Empirical BER Calculation: {bit_errors} errors / {len(tx_bits)} bits = {ber:.6f}")
    return ber


def calculate_theoretical_ber(modulation_type: str, eb_n0_db: float) -> float:
    """
    Computes the theoretical Bit Error Rate (BER) for a given modulation over an AWGN channel.
    
    For BPSK and QPSK:
        BER = Q(sqrt(2 * Eb/N0)) = 0.5 * erfc(sqrt(Eb/N0_linear))
        
    Args:
        modulation_type: Modulation format ('BPSK' or 'QPSK').
        eb_n0_db: Energy per Bit to Noise ratio in dB.
        
    Returns:
        float: Theoretical Bit Error Rate.
    """
    eb_n0_linear = 10 ** (eb_n0_db / 10.0)
    mod_upper = modulation_type.upper()

    if mod_upper in ["BPSK", "QPSK"]:
        # Q(sqrt(2 * Eb/N0)) = 0.5 * erfc(sqrt(Eb/N0))
        return 0.5 * erfc(np.sqrt(eb_n0_linear))
    elif mod_upper == "16QAM":
        # 16-QAM (Gray coded) theoretical BER
        # Pb = (3/8) * erfc(sqrt(2/5 * Eb/N0))
        return (3.0 / 8.0) * erfc(np.sqrt(0.4 * eb_n0_linear))
    elif mod_upper == "64QAM":
        # 64-QAM (Gray coded) theoretical BER
        # Pb = (7/24) * erfc(sqrt(1/7 * Eb/N0))
        return (7.0 / 24.0) * erfc(np.sqrt((1.0 / 7.0) * eb_n0_linear))
    else:
        logger.warning(f"Theoretical BER calculations not implemented for '{modulation_type}'. Returning 0.0.")
        return 0.0


def calculate_evm(tx_symbols: np.ndarray, rx_symbols: np.ndarray) -> float:
    """
    Computes the Error Vector Magnitude (EVM) in RMS percentage.
    
    EVM_RMS = sqrt( mean(|S_rx - S_tx|^2) / mean(|S_tx|^2) ) * 100
    
    Args:
        tx_symbols: 1D complex array of ideal transmitted symbols.
        rx_symbols: 1D complex array of received/synchronized symbols.
        
    Returns:
        float: RMS EVM percentage.
    """
    if len(tx_symbols) != len(rx_symbols):
        min_len = min(len(tx_symbols), len(rx_symbols))
        tx_symbols = tx_symbols[:min_len]
        rx_symbols = rx_symbols[:min_len]

    if len(tx_symbols) == 0:
        return 0.0

    error_vectors = rx_symbols - tx_symbols
    mean_error_power = np.mean(np.abs(error_vectors) ** 2)
    mean_reference_power = np.mean(np.abs(tx_symbols) ** 2)

    if mean_reference_power == 0:
        return 0.0

    evm_rms = np.sqrt(mean_error_power / mean_reference_power) * 100.0
    return float(evm_rms)


def calculate_snr_db(signal_power: float, noise_power: float) -> float:
    """
    Computes Signal-to-Noise Ratio (SNR) in decibels.
    
    Args:
        signal_power: Signal power in Watts.
        noise_power: Noise power in Watts.
        
    Returns:
        float: SNR in dB.
    """
    if noise_power <= 0:
        return float("inf")
    if signal_power <= 0:
        return float("-inf")
    return float(10.0 * np.log10(signal_power / noise_power))
