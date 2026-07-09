"""
Example script showing how to run a full SNR-vs-BER sweep using SDRLab.
Loads parameters from the default config.json file.
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
    # 1. Resolve path to default config.json
    config_path = project_root / "config.json"
    if not config_path.exists():
        logger.error(f"Default configuration file not found at: {config_path}")
        sys.exit(1)

    logger.info(f"Loading configuration file: {config_path}")
    
    # 2. Load Config and Controller
    try:
        config = SimulationConfig.load_from_json(str(config_path))
        # Override to ensure we generate plots and reports for demonstration
        config.generate_plots = True
        config.generate_reports = True
        
        controller = SimulationController(config)
        
        # 3. Execute sweep
        results_df = controller.execute_sweep()
        
        print("\n" + "="*60)
        print("SIMULATION SWEEP DATA PREVIEW")
        print("="*60)
        print(results_df.to_string(index=False))
        print("="*60)
        print(f"Results, logs, plots, and report saved under '{config.output_dir}/' directory.")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.exception(f"An error occurred during the sweep example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
