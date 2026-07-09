"""
Unit tests for SDRLab Configuration module (config.py).
Verifies parsing validation limits and error handling.
"""

import unittest
from sdrlab.config import SimulationConfig, SNRRange, ChannelImpairments


class TestSimulationConfig(unittest.TestCase):
    """Verifies that config loading, value boundaries, and validation errors work as designed."""

    def setUp(self) -> None:
        self.valid_data = {
            "engine": "auto",
            "num_bits": 10000,
            "sample_rate": 1000000,
            "sps": 4,
            "excess_bw": 0.35,
            "filter_span": 8,
            "modulations": ["BPSK", "QPSK"],
            "snr_db_range": {
                "start": 0.0,
                "stop": 10.0,
                "step": 2.0
            },
            "channel_impairments": {
                "cfo_hz": 50.0,
                "phase_noise_var": 0.01,
                "multipath_taps": [1.0, 0.1]
            },
            "outputs": {
                "output_dir": "test_outputs",
                "generate_plots": False,
                "generate_reports": False
            }
        }

    def test_valid_config_parsing(self) -> None:
        config = SimulationConfig(self.valid_data)
        self.assertEqual(config.engine, "auto")
        self.assertEqual(config.num_bits, 10000)
        self.assertEqual(config.sps, 4)
        self.assertEqual(config.excess_bw, 0.35)
        self.assertEqual(config.filter_span, 8)
        self.assertEqual(config.modulations, ["BPSK", "QPSK"])
        self.assertEqual(config.output_dir, "test_outputs")
        self.assertFalse(config.generate_plots)
        
        # Test SNR range generation
        snrs = config.snr_range.to_list()
        self.assertEqual(snrs, [0.0, 2.0, 4.0, 6.0, 8.0, 10.0])

    def test_invalid_engine_raises_error(self) -> None:
        data = self.valid_data.copy()
        data["engine"] = "invalid_engine_name"
        with self.assertRaises(ValueError):
            SimulationConfig(data)

    def test_negative_values_raise_error(self) -> None:
        # Check num_bits
        data = self.valid_data.copy()
        data["num_bits"] = -100
        with self.assertRaises(ValueError):
            SimulationConfig(data)
            
        # Check sample_rate
        data = self.valid_data.copy()
        data["sample_rate"] = 0
        with self.assertRaises(ValueError):
            SimulationConfig(data)

        # Check SPS
        data = self.valid_data.copy()
        data["sps"] = 1  # must be > 1
        with self.assertRaises(ValueError):
            SimulationConfig(data)

    def test_invalid_excess_bandwidth_limits(self) -> None:
        data = self.valid_data.copy()
        data["excess_bw"] = 1.2
        with self.assertRaises(ValueError):
            SimulationConfig(data)

        data["excess_bw"] = -0.1
        with self.assertRaises(ValueError):
            SimulationConfig(data)

    def test_unsupported_modulations_raise_error(self) -> None:
        data = self.valid_data.copy()
        data["modulations"] = ["INVALID_MOD"]
        with self.assertRaises(ValueError):
            SimulationConfig(data)

        # Test V1 unimplemented modules check (e.g. 16QAM)
        data["modulations"] = ["16QAM"]
        with self.assertRaises(ValueError):
            SimulationConfig(data)

    def test_invalid_snr_limits(self) -> None:
        data = self.valid_data.copy()
        data["snr_db_range"] = {"start": 10.0, "stop": 0.0, "step": 1.0}
        with self.assertRaises(ValueError):
            SimulationConfig(data)

        data["snr_db_range"] = {"start": 0.0, "stop": 10.0, "step": -1.0}
        with self.assertRaises(ValueError):
            SimulationConfig(data)


if __name__ == "__main__":
    unittest.main()
