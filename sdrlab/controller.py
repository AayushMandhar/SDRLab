"""
Simulation Controller for SDRLab.
Orchestrates sweeps, manages engine selections, executes simulation iterations, and triggers visualizers/reporters.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

from sdrlab.config import SimulationConfig
from sdrlab.logger import SDRLabLogger
from sdrlab.visualizer import SDRLabVisualizer
from sdrlab.reports import SimulationReporter

# DSP Imports
from sdrlab.dsp.transmitter import Transmitter
from sdrlab.dsp.channel import NoiseChannel
from sdrlab.dsp.receiver import Receiver
from sdrlab.dsp.synchronization import IdealTimingSynchronizer
from sdrlab.dsp.modulator import ModulatorFactory
from sdrlab.dsp.utils import rrc_filter

# GNU Radio Imports
from sdrlab.gnuradio.flowgraph import GNURADIO_AVAILABLE, GNURadioSimulationEngine, is_gnuradio_available

from sdrlab.metrics import (
    calculate_empirical_ber,
    calculate_theoretical_ber,
    calculate_evm,
    calculate_snr_db,
)

logger = SDRLabLogger.get_logger()


class SimulationController:
    """
    Coordinates the wireless communication simulation sweeps.
    Executes transmitter, channel, receiver, and metrics calculations for BPSK/QPSK.
    """

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.output_dir = Path(config.output_dir)
        
        # Setup Logger
        SDRLabLogger.setup_logger(output_dir=config.output_dir)
        
        # Determine engine backend
        self.engine_to_use = self._resolve_engine(config.engine)
        logger.info(f"Resolved Simulation Engine backend to: '{self.engine_to_use}'")

        # Initialize visualizer and reporter
        self.visualizer = SDRLabVisualizer(output_dir=config.output_dir)
        self.reporter = SimulationReporter(output_dir=config.output_dir)

    def _resolve_engine(self, requested_engine: str) -> str:
        """Resolves auto-detection of GNU Radio engine availability."""
        if requested_engine == "gnuradio":
            if not GNURADIO_AVAILABLE:
                raise RuntimeError("GNU Radio engine requested but not available on this system.")
            return "gnuradio"
        elif requested_engine == "simulation":
            return "simulation"
        else:  # "auto"
            if GNURADIO_AVAILABLE:
                logger.info("GNU Radio detected. Defaulting to GNU Radio Engine.")
                return "gnuradio"
            else:
                logger.warning("GNU Radio not detected. Falling back to Native Simulation Engine (NumPy/SciPy).")
                return "simulation"

    def _find_symbol_peak_delay(self, matched_signal: np.ndarray, tx_symbols: np.ndarray, sps: int) -> int:
        """
        Uses cross-correlation between the matched-filtered received signal and
        upsampled transmit symbols to find the exact delay lag.
        Ensures perfect symbol timing alignment.
        """
        # Upsample tx_symbols
        tx_upsampled = np.zeros(len(tx_symbols) * sps, dtype=complex)
        tx_upsampled[::sps] = tx_symbols
        
        # Perform cross-correlation on a prefix slice to save performance
        corr_len = min(2000, len(matched_signal), len(tx_upsampled))
        correlation = np.correlate(matched_signal[:corr_len], tx_upsampled[:corr_len], mode="full")
        
        # Find index of maximum correlation amplitude
        lag = np.argmax(np.abs(correlation)) - (corr_len - 1)
        
        # Ensure lag is non-negative and falls within range
        aligned_lag = int(max(0, lag))
        logger.debug(f"Cross-correlation alignment found symbol peak lag at sample index: {aligned_lag}")
        return aligned_lag

    def run_single_simulation(self, modulation: str, eb_n0_db: float) -> Dict[str, Any]:
        """
        Runs one iteration of simulation (transmitter -> channel -> receiver -> metrics)
        for a specific modulation and Eb/N0.
        """
        # Instantiate Native DSP Transmitter and Channel
        transmitter = Transmitter(
            modulation_type=modulation,
            sps=self.config.sps,
            filter_span=self.config.filter_span,
            excess_bw=self.config.excess_bw
        )
        
        channel = NoiseChannel(
            cfo_hz=self.config.channel_impairments.cfo_hz,
            phase_noise_var=self.config.channel_impairments.phase_noise_var,
            multipath_taps=self.config.channel_impairments.multipath_taps,
            sample_rate=self.config.sample_rate
        )

        # Generate Bits
        tx_bits = transmitter.generate_random_bits(self.config.num_bits)
        expected_syms = len(tx_bits) // transmitter.modulator.bits_per_symbol

        # Run Backend
        if self.engine_to_use == "gnuradio":
            gr_engine = GNURadioSimulationEngine(self.config)
            tx_waveform, noisy_waveform, rx_waveform = gr_engine.run_flowgraph(tx_bits, modulation, eb_n0_db)
            # Reconstruct ideal tx_symbols for alignment
            tx_symbols = transmitter.modulator.map_bits_to_symbols(tx_bits)
            # Measure signal and noise power from GNU Radio waveforms
            # Note: channel model output = faded signal + noise
            sig_pwr = float(np.mean(np.abs(tx_waveform) ** 2))
            # Rough estimate of noise power: total power - signal power
            total_noisy_pwr = np.mean(np.abs(noisy_waveform) ** 2)
            noise_pwr = float(max(1e-12, total_noisy_pwr - sig_pwr))
        else:
            # Native Engine
            tx_waveform, tx_symbols = transmitter.transmit(tx_bits)
            noisy_waveform, sig_pwr, noise_pwr = channel.propagate(
                tx_waveform,
                eb_n0_db,
                transmitter.modulator.bits_per_symbol,
                self.config.sps
            )
            # Matched filter locally to align correlation
            rx_rrc = rrc_filter(self.config.sps, self.config.filter_span, self.config.excess_bw)
            rx_waveform = np.convolve(noisy_waveform, rx_rrc, mode="full")

        # 1. Align timing peak using cross-correlation
        peak_delay = self._find_symbol_peak_delay(rx_waveform, tx_symbols, self.config.sps)
        
        # 2. Instantiate receiver using the aligned timing recovery
        timing_sync = IdealTimingSynchronizer(filter_delay_samples=peak_delay)
        receiver = Receiver(
            modulation_type=modulation,
            sps=self.config.sps,
            filter_span=self.config.filter_span,
            excess_bw=self.config.excess_bw,
            timing_sync=timing_sync
        )
        
        # 3. Process matched filtering and symbol recovery
        rx_bits, rx_symbols = receiver.receive(noisy_waveform, expected_syms)

        # Calculate Metrics
        empirical_ber = calculate_empirical_ber(tx_bits, rx_bits)
        theoretical_ber = calculate_theoretical_ber(modulation, eb_n0_db)
        evm_value = calculate_evm(tx_symbols, rx_symbols)
        measured_snr = calculate_snr_db(sig_pwr, noise_pwr)

        logger.info(
            f"Results [{modulation} @ {eb_n0_db}dB]: BER={empirical_ber:.6f} "
            f"(Theory={theoretical_ber:.6f}), EVM={evm_value:.2f}%, SNR={measured_snr:.2f}dB"
        )

        return {
            "modulation": modulation,
            "eb_n0_db": eb_n0_db,
            "empirical_ber": empirical_ber,
            "theoretical_ber": theoretical_ber,
            "evm_percent": evm_value,
            "measured_snr_db": measured_snr,
            "signal_power_w": sig_pwr,
            "noise_power_w": noise_pwr,
            # Return raw arrays for plotting
            "_tx_waveform": tx_waveform,
            "_noisy_waveform": noisy_waveform,
            "_tx_symbols": tx_symbols,
            "_rx_symbols": rx_symbols,
        }

    def execute_sweep(self) -> pd.DataFrame:
        """
        Executes simulation sweeps across configured modulations and SNR values.
        Generates plots, CSV data, and a final Markdown report.
        """
        logger.info("Starting SDRLab simulation sweep...")
        
        snr_vals = self.config.snr_range.to_list()
        sweep_data = []
        
        # Record file paths for report generation
        generated_figures = {}
        
        for mod in self.config.modulations:
            generated_figures[mod] = []
            logger.info(f"Sweeping modulation: {mod} across SNR: {snr_vals} dB")
            
            for snr in snr_vals:
                run_metrics = self.run_single_simulation(mod, snr)
                sweep_data.append({
                    "Modulation": run_metrics["modulation"],
                    "Eb_N0_dB": run_metrics["eb_n0_db"],
                    "Empirical_BER": run_metrics["empirical_ber"],
                    "Theoretical_BER": run_metrics["theoretical_ber"],
                    "EVM_Percent": run_metrics["evm_percent"],
                    "Measured_SNR_dB": run_metrics["measured_snr_db"],
                    "Signal_Power_W": run_metrics["signal_power_w"],
                    "Noise_Power_W": run_metrics["noise_power_w"],
                })
                
                # Plot detailed figures for a subset of SNRs (e.g. 0dB, 6dB, 12dB) to avoid generating too many files
                if self.config.generate_plots and snr in [0.0, 6.0, 12.0, min(snr_vals), max(snr_vals)]:
                    c_file = f"{mod}_constellation_snr_{int(snr)}.png"
                    w_file = f"{mod}_waveform_snr_{int(snr)}.png"
                    p_file = f"{mod}_psd_snr_{int(snr)}.png"
                    
                    c_path = self.visualizer.plot_constellations(
                        run_metrics["_tx_symbols"],
                        # Approximate unsynchronized symbols by downsampling raw noisy waveform (for comparison visual)
                        run_metrics["_noisy_waveform"][::self.config.sps][:len(run_metrics["_tx_symbols"])],
                        run_metrics["_rx_symbols"],
                        mod,
                        snr,
                        filename=c_file
                    )
                    
                    w_path = self.visualizer.plot_waveform(
                        run_metrics["_tx_waveform"],
                        run_metrics["_noisy_waveform"],
                        self.config.sample_rate,
                        filename=w_file
                    )
                    
                    p_path = self.visualizer.plot_psd(
                        run_metrics["_tx_waveform"],
                        run_metrics["_noisy_waveform"],
                        self.config.sample_rate,
                        filename=p_file
                    )
                    
                    generated_figures[mod].append({
                        "snr": snr,
                        "constellation": c_path,
                        "waveform": w_path,
                        "psd": p_path
                    })

        results_df = pd.DataFrame(sweep_data)
        
        # Plot consolidated BER sweep curves
        ber_curve_path = ""
        if self.config.generate_plots:
            ber_results_dict = {}
            for mod in self.config.modulations:
                mod_df = results_df[results_df["Modulation"] == mod]
                ber_results_dict[mod] = mod_df["Empirical_BER"].tolist()
            
            ber_curve_path = self.visualizer.plot_ber_curves(
                snr_vals,
                ber_results_dict,
                filename="ber_vs_snr.png"
            )

        # Assemble markdown report
        if self.config.generate_reports:
            self.reporter.generate_report(
                config=self.config,
                results_df=results_df,
                generated_figures=generated_figures,
                ber_curve_path=ber_curve_path
            )

        logger.info("SDRLab simulation sweep execution finished successfully.")
        return results_df
