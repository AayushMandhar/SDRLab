"""
Simulation runner wrapper for the SDRLab Streamlit app.
Integrates UI inputs with the existing SDRLab controller and configurations.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

# Add the project root to python path to import sdrlab package
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sdrlab.config import SimulationConfig
from sdrlab.controller import SimulationController
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


def run_sdrlab_simulation(
    engine: str,
    modulation: str,
    snr_start: float,
    snr_stop: float,
    snr_step: float,
    num_bits: int,
    sps: int,
    sample_rate: int,
    cfo_hz: float,
    phase_noise_var: float,
    multipath_taps: str,
    generate_plots: bool,
    generate_reports: bool,
) -> Tuple[pd.DataFrame, str]:
    """
    Constructs a SimulationConfig and runs the SimulationController sweep.
    
    Args:
        engine: "auto", "simulation", or "gnuradio".
        modulation: "BPSK", "QPSK", or a list.
        snr_start: Range start.
        snr_stop: Range end.
        snr_step: Range step.
        num_bits: Number of bits.
        sps: Samples per symbol.
        sample_rate: Sample rate in Hz.
        cfo_hz: Carrier Frequency Offset.
        phase_noise_var: Phase noise variance.
        multipath_taps: Commas-separated tap values (e.g. "1.0, 0.2, 0.05").
        generate_plots: Enable plot exports.
        generate_reports: Enable report exports.
        
    Returns:
        Tuple[pd.DataFrame, str]: Result DataFrame and a status message.
    """
    # 1. Parse multipath taps
    try:
        taps_list = [float(x.strip()) for x in multipath_taps.split(",") if x.strip()]
        if not taps_list:
            taps_list = [1.0]
    except Exception as e:
        logger.warning(f"Error parsing multipath taps: {e}. Defaulting to [1.0].")
        taps_list = [1.0]

    # 2. Build configuration dictionary
    config_dict = {
        "engine": engine,
        "num_bits": num_bits,
        "sample_rate": sample_rate,
        "sps": sps,
        "excess_bw": 0.35,  # standard default
        "filter_span": 8,   # standard default
        "modulations": [modulation],
        "snr_db_range": {
            "start": snr_start,
            "stop": snr_stop,
            "step": snr_step
        },
        "channel_impairments": {
            "cfo_hz": cfo_hz,
            "phase_noise_var": phase_noise_var,
            "multipath_taps": taps_list
        },
        "outputs": {
            "output_dir": "outputs",
            "generate_plots": generate_plots,
            "generate_reports": generate_reports
        }
    }

    # 3. Initialize config and controller
    config = SimulationConfig(config_dict)
    controller = SimulationController(config)
    
    # 4. Execute the simulation sweep
    logger.info("Executing simulation from Streamlit dashboard UI...")
    results_df = controller.execute_sweep()
    
    status = f"Simulation successfully completed using engine: '{controller.engine_to_use}'."
    return results_df, status
