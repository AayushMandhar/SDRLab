"""
Visualizer module for SDRLab.
Generates matplotlib plots for constellations, PSD, FFT, time waveforms, and BER curves.
Uses the headless 'Agg' backend to ensure compatibility with CLI/server environments.
"""

import os
from pathlib import Path
from typing import List, Optional
import numpy as np

# Set matplotlib to non-interactive Agg backend to avoid GUI window popups in headless systems
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


class SDRLabVisualizer:
    """
    Handles plotting for SDR simulations.
    All plots are saved to the filesystem under outputs/plots/ or outputs/figures/.
    """

    def __init__(self, output_dir: str = "outputs") -> None:
        self.output_dir = Path(output_dir)
        self.plots_dir = self.output_dir / "plots"
        self.figures_dir = self.output_dir / "figures"
        
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Apply clean visual styles
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams.update({
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "figure.titlesize": 14,
            "grid.alpha": 0.4,
        })

    def plot_waveform(
        self,
        tx_waveform: np.ndarray,
        noisy_waveform: np.ndarray,
        sample_rate: int,
        num_symbols_to_show: int = 15,
        sps: int = 4,
        filename: str = "waveform_time.png",
    ) -> str:
        """
        Plots a snippet of the transmitted and noisy received time-domain complex waveforms (Real parts).
        """
        num_samples = num_symbols_to_show * sps
        if len(tx_waveform) < num_samples:
            num_samples = len(tx_waveform)
            
        t = np.arange(num_samples) / float(sample_rate) * 1e6  # Microseconds
        
        fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        
        # Tx waveform
        axes[0].plot(t, tx_waveform[:num_samples].real, color="#0A2540", linewidth=1.5, label="In-phase (I)")
        axes[0].plot(t, tx_waveform[:num_samples].imag, color="#639FAB", linewidth=1.0, alpha=0.7, label="Quadrature (Q)")
        axes[0].set_title("Transmitted Baseband Waveform (Filtered & Pulse-Shaped)")
        axes[0].set_ylabel("Amplitude")
        axes[0].grid(True)
        axes[0].legend(loc="upper right")
        
        # Noisy waveform
        axes[1].plot(t, noisy_waveform[:num_samples].real, color="#E28743", linewidth=1.2, label="Noisy I")
        axes[1].plot(t, noisy_waveform[:num_samples].imag, color="#76b5c5", linewidth=0.8, alpha=0.7, label="Noisy Q")
        axes[1].set_title("Received Waveform (Noisy Channel Output)")
        axes[1].set_xlabel("Time (microseconds)")
        axes[1].set_ylabel("Amplitude")
        axes[1].grid(True)
        axes[1].legend(loc="upper right")
        
        plt.tight_layout()
        save_path = self.figures_dir / filename
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
        
        logger.debug(f"Time waveform plot saved to {save_path}")
        return str(save_path.resolve())

    def plot_constellations(
        self,
        tx_symbols: np.ndarray,
        noisy_symbols: np.ndarray,
        rx_symbols: np.ndarray,
        modulation: str,
        snr_db: float,
        filename: str = "constellation.png",
    ) -> str:
        """
        Generates comparison scatter plots of constellations at three points in the receiver pipeline:
        1. Ideal Transmitted Symbols
        2. Unsynchronized Noisy Symbols (extracted prior to match filtering or synchronization)
        3. Restored/Demapped Symbols
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)
        
        # Max axis limit based on constellations
        lim = 2.0
        
        # 1. Ideal Tx
        axes[0].scatter(tx_symbols.real, tx_symbols.imag, color="#0A2540", alpha=0.6, s=15, edgecolors="none")
        axes[0].set_title("1. Ideal Tx Symbols")
        axes[0].set_xlabel("In-Phase")
        axes[0].set_ylabel("Quadrature")
        axes[0].grid(True)
        axes[0].set_xlim(-lim, lim)
        axes[0].set_ylim(-lim, lim)
        axes[0].axhline(0, color="black", linewidth=0.5)
        axes[0].axvline(0, color="black", linewidth=0.5)
        
        # 2. Noisy Channel Output
        axes[1].scatter(noisy_symbols.real, noisy_symbols.imag, color="#D9534F", alpha=0.4, s=8, edgecolors="none")
        axes[1].set_title(f"2. Noisy Symbols (SNR: {snr_db}dB)")
        axes[1].set_xlabel("In-Phase")
        axes[1].grid(True)
        axes[1].axhline(0, color="black", linewidth=0.5)
        axes[1].axvline(0, color="black", linewidth=0.5)
        
        # 3. Rx symbols after Matched Filter & Sync
        axes[2].scatter(rx_symbols.real, rx_symbols.imag, color="#2ECC71", alpha=0.5, s=12, edgecolors="none")
        axes[2].set_title("3. Rx Recovered Symbols")
        axes[2].set_xlabel("In-Phase")
        axes[2].grid(True)
        axes[2].axhline(0, color="black", linewidth=0.5)
        axes[2].axvline(0, color="black", linewidth=0.5)
        
        plt.suptitle(f"{modulation} Constellation Analysis (SNR={snr_db} dB)", y=0.98)
        plt.tight_layout()
        save_path = self.figures_dir / filename
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
        
        logger.debug(f"Constellation plot saved to {save_path}")
        return str(save_path.resolve())

    def plot_psd(
        self,
        tx_waveform: np.ndarray,
        noisy_waveform: np.ndarray,
        sample_rate: int,
        filename: str = "psd_spectrum.png",
    ) -> str:
        """
        Computes and plots the Power Spectral Density (PSD) using Welch's method.
        Shows filter shape, spectral containment, and noise floor.
        """
        from scipy.signal import welch
        
        fs_mhz = sample_rate / 1e6
        
        # Compute PSD
        f_tx, psd_tx = welch(tx_waveform, fs=fs_mhz, nperseg=1024, return_onesided=False)
        f_noisy, psd_noisy = welch(noisy_waveform, fs=fs_mhz, nperseg=1024, return_onesided=False)
        
        # Shift frequencies to center at DC
        f_tx = np.fft.fftshift(f_tx)
        psd_tx = np.fft.fftshift(psd_tx)
        
        f_noisy = np.fft.fftshift(f_noisy)
        psd_noisy = np.fft.fftshift(psd_noisy)
        
        # Normalize to max power dB
        psd_tx_db = 10 * np.log10(psd_tx / np.max(psd_tx))
        psd_noisy_db = 10 * np.log10(psd_noisy / np.max(psd_noisy))
        
        plt.figure(figsize=(10, 5))
        plt.plot(f_tx, psd_tx_db, color="#0A2540", linewidth=1.5, label="Transmitted Signal (RRC Pulse)")
        plt.plot(f_noisy, psd_noisy_db, color="#E28743", linewidth=1.0, alpha=0.8, label="Noisy Received Signal")
        
        plt.title("Power Spectral Density (Welch Periodogram)")
        plt.xlabel("Frequency Offset (MHz)")
        plt.ylabel("Normalized Power Spectral Density (dB)")
        plt.ylim(-60, 5)
        plt.xlim(-fs_mhz / 2, fs_mhz / 2)
        plt.grid(True, which="both", linestyle="--")
        plt.legend(loc="upper right")
        
        plt.tight_layout()
        save_path = self.figures_dir / filename
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
        
        logger.debug(f"PSD spectrum plot saved to {save_path}")
        return str(save_path.resolve())

    def plot_ber_curves(
        self,
        snr_range: List[float],
        results: dict,  # Dict mapping Mod -> list of empirical BERs
        filename: str = "ber_vs_snr.png",
    ) -> str:
        """
        Plots a BER vs SNR waterfall curve, overlaying empirical sweeps against theoretical limits.
        """
        from sdrlab.metrics import calculate_theoretical_ber
        
        plt.figure(figsize=(9, 6))
        
        colors = {"BPSK": "#008080", "QPSK": "#FF4500", "16QAM": "#4B0082", "64QAM": "#228B22"}
        
        snr_dense = np.linspace(min(snr_range), max(snr_range), 100)
        
        for mod, empirical_bers in results.items():
            color = colors.get(mod, "#333333")
            
            # 1. Plot Theoretical Limit curve (dense points for smooth line)
            theory_bers = [calculate_theoretical_ber(mod, s) for s in snr_dense]
            plt.semilogy(snr_dense, theory_bers, color=color, linestyle="--", linewidth=1.5, label=f"{mod} Theoretical")
            
            # 2. Plot Empirical Sweep points
            plt.semilogy(snr_range, empirical_bers, color=color, marker="o", markersize=6, linestyle="-", linewidth=2.0, label=f"{mod} Empirical")
            
        plt.title("Bit Error Rate (BER) vs Eb/N0 Performance")
        plt.xlabel("Eb/N0 (dB)")
        plt.ylabel("Bit Error Rate (Log scale)")
        plt.ylim(1e-5, 1.0)
        plt.grid(True, which="both", linestyle=":")
        plt.legend(loc="lower left")
        
        plt.tight_layout()
        save_path = self.plots_dir / filename
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
        
        logger.debug(f"BER curves sweep plot saved to {save_path}")
        return str(save_path.resolve())
