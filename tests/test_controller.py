"""
Integration tests for SDRLab Simulation Controller (controller.py).
Runs micro-simulations to verify sweep execution logic.
"""

import unittest
from sdrlab.config import SimulationConfig
from sdrlab.controller import SimulationController


class TestSimulationControllerIntegration(unittest.TestCase):
    """Verifies that the controller executes sweeps without exceptions."""

    def test_micro_sweep_execution(self) -> None:
        # Micro sweep configuration to run instantly in memory
        config_data = {
            "engine": "simulation",  # Force native DSP engine
            "num_bits": 1000,
            "sample_rate": 100000,
            "sps": 4,
            "excess_bw": 0.35,
            "filter_span": 4,
            "modulations": ["BPSK", "QPSK"],
            "snr_db_range": {
                "start": 2.0,
                "stop": 4.0,
                "step": 2.0
            },
            "channel_impairments": {
                "cfo_hz": 0.0,
                "phase_noise_var": 0.0,
                "multipath_taps": [1.0]
            },
            "outputs": {
                "output_dir": "outputs_test",  # Separate directory
                "generate_plots": False,
                "generate_reports": False
            }
        }

        config = SimulationConfig(config_data)
        controller = SimulationController(config)
        
        # Verify resolved engine
        self.assertEqual(controller.engine_to_use, "simulation")
        
        # Execute sweep
        results_df = controller.execute_sweep()
        
        # Verify DataFrame properties
        self.assertIsNotNone(results_df)
        self.assertFalse(results_df.empty)
        
        # Expected rows: 2 modulations * 2 SNR values = 4 rows
        self.assertEqual(len(results_df), 4)
        
        # Columns checklist
        expected_cols = {
            "Modulation",
            "Eb_N0_dB",
            "Empirical_BER",
            "Theoretical_BER",
            "EVM_Percent",
            "Measured_SNR_dB",
            "Signal_Power_W",
            "Noise_Power_W",
        }
        self.assertTrue(expected_cols.issubset(results_df.columns))
        
        # Clean up output directory if created
        import shutil
        from pathlib import Path
        from sdrlab.logger import SDRLabLogger
        SDRLabLogger.shutdown()
        
        test_out = Path("outputs_test")
        if test_out.exists():
            shutil.rmtree(test_out)


if __name__ == "__main__":
    unittest.main()
