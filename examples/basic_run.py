"""
Example script showing programmatic usage of SDRLab API.
Runs a single simulation run for QPSK at 8.0 dB SNR using the resolved engine.
"""

import sys
from pathlib import Path

# Add project root directory to path to ensure sdrlab package is importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sdrlab.config import SimulationConfig
from sdrlab.controller import SimulationController
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


def main() -> None:
    # 1. Define configuration dictionary programmatically
    config_data = {
        "engine": "auto",
        "num_bits": 20000,
        "sample_rate": 1000000,
        "sps": 4,
        "excess_bw": 0.35,
        "filter_span": 8,
        "modulations": ["QPSK"],
        "snr_db_range": {
            "start": 8.0,
            "stop": 8.0,
            "step": 1.0
        },
        "channel_impairments": {
            "cfo_hz": 0.0,
            "phase_noise_var": 0.0,
            "multipath_taps": [1.0]
        },
        "outputs": {
            "output_dir": "outputs",
            "generate_plots": True,
            "generate_reports": True
        }
    }

    logger.info("Initializing SDRLab basic simulation run...")
    
    # 2. Instantiate Config and Controller
    config = SimulationConfig(config_data)
    controller = SimulationController(config)
    
    # 3. Execute a single SNR run directly using the API
    modulation = "QPSK"
    snr_db = 8.0
    
    logger.info(f"Executing direct simulation: modulation={modulation}, SNR={snr_db}dB")
    metrics = controller.run_single_simulation(modulation=modulation, eb_n0_db=snr_db)
    
    print("\n" + "="*50)
    print("SIMULATION RESULTS")
    print("="*50)
    print(f"Modulation Format:    {metrics['modulation']}")
    print(f"Requested Eb/N0:      {metrics['eb_n0_db']:.2f} dB")
    print(f"Empirical BER:        {metrics['empirical_ber']:.6f}")
    print(f"Theoretical BER:      {metrics['theoretical_ber']:.6f}")
    print(f"EVM (RMS %):          {metrics['evm_percent']:.2f}%")
    print(f"Measured SNR:         {metrics['measured_snr_db']:.2f} dB")
    print(f"Signal Power:         {metrics['signal_power_w']:.6f} Watts")
    print(f"Noise Power:          {metrics['noise_power_w']:.6f} Watts")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
