"""
GNU Radio flowgraph wrapper module for SDRLab.
Constructs a gr.top_block flowgraph programmatically using GNU Radio Python bindings.
Provides a fallback mechanism if GNU Radio is not installed.
"""

import numpy as np
from typing import Dict, List, Tuple, Any

# Dynamic import of GNU Radio blocks with a boolean flag
try:
    from gnuradio import gr, digital, analog, channels, blocks, filter
    GNURADIO_AVAILABLE = True
except ImportError:
    GNURADIO_AVAILABLE = False

from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


def is_gnuradio_available() -> bool:
    """Returns True if GNU Radio python bindings are available on this system."""
    return GNURADIO_AVAILABLE


class GNURadioSimulationEngine:
    """
    Orchestrates the simulation using the GNU Radio execution engine.
    Constructs and runs the top block flowgraph.
    """

    def __init__(self, config: Any) -> None:
        """
        Initializes the GNU Radio simulation engine.
        
        Args:
            config: An instance of SimulationConfig.
        """
        if not GNURADIO_AVAILABLE:
            raise RuntimeError(
                "GNU Radio is not installed or not found in Python path. "
                "Cannot initialize GNURadioSimulationEngine."
            )
        self.config = config

    def run_flowgraph(
        self, bits: np.ndarray, modulation: str, eb_n0_db: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Runs the programmatic GNU Radio flowgraph for a given SNR and modulation.
        
        Args:
            bits: 1D numpy array of binary bits to transmit.
            modulation: Modulation type (e.g. 'BPSK', 'QPSK').
            eb_n0_db: SNR Eb/N0 in dB.
            
        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]:
                - tx_waveform: The filtered, modulated waveform from the transmitter.
                - noisy_waveform: The channel impaired waveform.
                - rx_waveform: The matched-filtered received waveform.
        """
        logger.info(f"Running GNU Radio flowgraph for {modulation} at Eb/N0={eb_n0_db:.2f}dB")

        # 1. Setup Constellation
        mod_upper = modulation.upper()
        if mod_upper == "BPSK":
            constel = digital.constellation_bpsk().base()
            bits_per_symbol = 1
        elif mod_upper == "QPSK":
            constel = digital.constellation_qpsk().base()
            bits_per_symbol = 2
        else:
            raise ValueError(f"Modulation '{modulation}' not supported by GNU Radio engine in V1.")

        # 2. Calculate Channel Parameters
        # Calculate noise voltage based on Eb/N0
        # Es/N0 = Eb/N0 + 10*log10(bits_per_symbol)
        # SNR_sample = Es/N0 - 10*log10(sps)
        es_n0_db = eb_n0_db + 10.0 * np.log10(bits_per_symbol)
        snr_db = es_n0_db - 10.0 * np.log10(self.config.sps)
        snr_linear = 10.0 ** (snr_db / 10.0)
        
        # GNU Radio channel model noise voltage is the standard deviation of complex noise.
        # Since constellation average power is 1.0, noise_voltage = sqrt(1.0 / SNR_sample)
        noise_voltage = np.sqrt(1.0 / snr_linear)

        # CFO normalized: CFO_hz / sample_rate
        norm_cfo = self.config.channel_impairments.cfo_hz / float(self.config.sample_rate)
        
        # Multipath taps
        taps = [complex(t) for t in self.config.channel_impairments.multipath_taps]

        # 3. Design Matched Filter Coefficients
        # We generate the RRC coefficients for the receiver matched filter block
        # GNU Radio firdes is used
        rx_rrc_coeffs = filter.firdes.root_raised_cosine(
            1.0,                                    # Gain
            float(self.config.sps),                # Sampling frequency (normalized)
            1.0,                                    # Symbol rate
            self.config.excess_bw,                 # Excess BW (alpha)
            self.config.filter_span * self.config.sps + 1  # Number of taps
        )

        # 4. Construct Flowgraph
        tb = gr.top_block("SDRLab Flowgraph")

        # Source: feeds the bits
        # Note: Vector source expects unsigned bytes (uint8)
        bits_uint8 = bits.astype(np.uint8)
        src = blocks.vector_source_b(bits_uint8.tolist(), False)

        # Modulator Chaining (equivalent to digital.constellation_modulator, compatible with GNU Radio 3.10)
        # 1. Bit Pack: group bits into symbol indices (k bits per symbol)
        pack = blocks.pack_k_bits_bb(bits_per_symbol)
        
        # 2. Map indices to complex symbols with exact bit-ordering matching the native modulator
        from sdrlab.dsp.modulator import ModulatorFactory
        mod_obj = ModulatorFactory.get_modulator(modulation)
        points_list = []
        for idx in range(2**bits_per_symbol):
            idx_bits = np.array([int(b) for b in format(idx, f"0{bits_per_symbol}b")], dtype=int)
            symbol = mod_obj.map_bits_to_symbols(idx_bits)[0]
            points_list.append(complex(symbol))
            
        mapper = digital.chunks_to_symbols_bc(points_list)
        
        # 3. Interpolating FIR Filter for RRC pulse shaping
        tx_rrc_coeffs = filter.firdes.root_raised_cosine(
            1.0,                                          # Gain
            float(self.config.sps),                      # Sampling frequency
            1.0,                                          # Symbol rate
            self.config.excess_bw,                       # Excess BW (alpha)
            self.config.filter_span * self.config.sps + 1 # Number of taps
        )
        pulse_shaper = filter.interp_fir_filter_ccf(
            self.config.sps,
            tx_rrc_coeffs
        )

        # Channel Model
        # Parameters: noise_voltage, frequency_offset, epsilon, taps, noise_seed
        channel = channels.channel_model(
            noise_voltage,
            norm_cfo,
            1.0,  # Epsilon (timing offset = 1.0 means none)
            taps,
            42    # Seed
        )

        # Matched Filter
        matched_filter = filter.fir_filter_ccf(
            1,  # Decimation factor (we keep at 1 and synchronize in Python)
            rx_rrc_coeffs
        )

        # Sinks
        tx_sink = blocks.vector_sink_c()
        channel_sink = blocks.vector_sink_c()
        rx_sink = blocks.vector_sink_c()

        # Connect blocks
        # src -> pack -> mapper -> pulse_shaper -> tx_sink
        tb.connect(src, pack)
        tb.connect(pack, mapper)
        tb.connect(mapper, pulse_shaper)
        tb.connect(pulse_shaper, tx_sink)

        # pulse_shaper -> channel -> channel_sink
        tb.connect(pulse_shaper, channel)
        tb.connect(channel, channel_sink)

        # channel -> matched_filter -> rx_sink
        tb.connect(channel, matched_filter)
        tb.connect(matched_filter, rx_sink)

        # 5. Run Flowgraph
        tb.run()

        # 6. Retrieve Vector Sinks Data
        tx_waveform = np.array(tx_sink.data(), dtype=complex)
        noisy_waveform = np.array(channel_sink.data(), dtype=complex)
        rx_waveform = np.array(rx_sink.data(), dtype=complex)

        logger.debug(
            f"GNU Radio completed: Tx samples={len(tx_waveform)}, "
            f"Noisy samples={len(noisy_waveform)}, Rx samples={len(rx_waveform)}"
        )

        return tx_waveform, noisy_waveform, rx_waveform
