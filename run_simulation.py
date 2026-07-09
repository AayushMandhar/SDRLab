"""
Main command-line interface entry point for SDRLab simulation framework.
Supports running custom configs, selecting backends, toggling visual outputs, and generating sweep reports.
"""

import argparse
import sys
from pathlib import Path

from sdrlab.config import SimulationConfig
from sdrlab.controller import SimulationController
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="SDRLab: Configurable Wireless Communication Simulation Framework using GNU Radio & NumPy."
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to JSON configuration file (default: config.json)"
    )
    
    parser.add_argument(
        "--engine",
        type=str,
        choices=["auto", "gnuradio", "simulation"],
        help="Override simulation engine backend (auto, gnuradio, or simulation)"
    )
    
    # Flags to toggle plot generation
    parser.add_argument(
        "--plot",
        dest="plot",
        action="store_true",
        default=None,
        help="Force enable plot generation (overrides config)"
    )
    parser.add_argument(
        "--no-plot",
        dest="plot",
        action="store_false",
        help="Force disable plot generation"
    )
    
    # Flags to toggle report generation
    parser.add_argument(
        "--report",
        dest="report",
        action="store_true",
        default=None,
        help="Force enable report generation (overrides config)"
    )
    parser.add_argument(
        "--no-report",
        dest="report",
        action="store_false",
        help="Force disable report generation"
    )

    return parser.parse_args()


def main() -> None:
    print("\n" + "="*70)
    print(" SDRLab: Configurable Wireless Communication Simulation Framework")
    print("="*70)
    
    args = parse_arguments()
    
    # 1. Load config from JSON file
    config_path = Path(args.config)
    if not config_path.exists():
        # If default config.json is not found in local dir, check relative to this script
        script_dir_config = Path(__file__).resolve().parent / "config.json"
        if script_dir_config.exists():
            config_path = script_dir_config
        else:
            print(f"Error: Configuration file not found at '{args.config}'.")
            print("Please create a 'config.json' file or specify a valid file path using '--config'.")
            sys.exit(1)

    try:
        logger.info(f"Loading configuration from: {config_path}")
        config = SimulationConfig.load_from_json(str(config_path))
        
        # 2. Apply command-line overrides
        if args.engine:
            config.engine = args.engine
            logger.info(f"CLI Override: Engine set to '{args.engine}'")
            
        if args.plot is not None:
            config.generate_plots = args.plot
            logger.info(f"CLI Override: Generate plots set to {args.plot}")
            
        if args.report is not None:
            config.generate_reports = args.report
            logger.info(f"CLI Override: Generate reports set to {args.report}")

        # 3. Instantiate and run sweep
        controller = SimulationController(config)
        results_df = controller.execute_sweep()
        
        print("\n" + "="*70)
        print(" SIMULATION SWEEP COMPLETED SUCCESSFULLY")
        print("="*70)
        print(f"Output files written to directory: {config.output_dir}/")
        print(f"  - Logs:           {config.output_dir}/logs/simulation.log")
        if config.generate_plots:
            print(f"  - Plots:          {config.output_dir}/plots/")
            print(f"  - Figures:        {config.output_dir}/figures/")
        if config.generate_reports:
            print(f"  - CSV Data:       {config.output_dir}/csv/sweep_results.csv")
            print(f"  - Markdown Report:{config.output_dir}/reports/simulation_report.md")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.exception(f"Fatal error occurred during execution: {e}")
        print(f"\nExecution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
