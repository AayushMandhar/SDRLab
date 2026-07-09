"""
Configuration manager for SDRLab.
Handles loading, validation, and serialization of simulation configurations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional


class SNRRange(NamedTuple):
    start: float
    stop: float
    step: float

    def to_list(self) -> List[float]:
        """Generates a list of SNR values from the range parameters."""
        import numpy as np
        # Use np.arange for decimal precision and float ranges
        if self.step <= 0:
            return [self.start]
        # Include endpoint if step aligns
        return [float(x) for x in np.arange(self.start, self.stop + 1e-9, self.step)]


class ChannelImpairments(NamedTuple):
    cfo_hz: float
    phase_noise_var: float
    multipath_taps: List[float]


class SimulationConfig:
    """
    Holds and validates simulation settings.
    """

    def __init__(self, raw_config: Dict[str, Any]) -> None:
        self._raw = raw_config
        self.engine: str = "auto"
        self.num_bits: int = 10000
        self.sample_rate: int = 1000000
        self.sps: int = 4
        self.excess_bw: float = 0.35
        self.filter_span: int = 8
        self.modulations: List[str] = ["BPSK"]
        self.snr_range: SNRRange = SNRRange(0.0, 10.0, 2.0)
        self.channel_impairments: ChannelImpairments = ChannelImpairments(
            cfo_hz=0.0, phase_noise_var=0.0, multipath_taps=[1.0]
        )
        self.output_dir: str = "outputs"
        self.generate_plots: bool = True
        self.generate_reports: bool = True

        self._parse_and_validate()

    def _parse_and_validate(self) -> None:
        """Parses raw config dictionary with schema checks."""
        # Engine
        self.engine = str(self._raw.get("engine", "auto")).lower()
        if self.engine not in ["auto", "simulation", "gnuradio"]:
            raise ValueError(f"Invalid engine type: '{self.engine}'. Must be 'auto', 'simulation', or 'gnuradio'.")

        # Basic signal parameters
        self.num_bits = int(self._raw.get("num_bits", 10000))
        if self.num_bits <= 0:
            raise ValueError("num_bits must be positive.")

        self.sample_rate = int(self._raw.get("sample_rate", 1000000))
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive.")

        self.sps = int(self._raw.get("sps", 4))
        if self.sps <= 1:
            raise ValueError("sps (samples per symbol) must be an integer > 1.")

        self.excess_bw = float(self._raw.get("excess_bw", 0.35))
        if not (0.0 <= self.excess_bw <= 1.0):
            raise ValueError("excess_bw must be between 0.0 and 1.0.")

        self.filter_span = int(self._raw.get("filter_span", 8))
        if self.filter_span <= 0:
            raise ValueError("filter_span must be positive.")

        # Modulations
        raw_mods = self._raw.get("modulations", ["BPSK"])
        if not isinstance(raw_mods, list) or not raw_mods:
            raise ValueError("modulations must be a non-empty list of strings.")
        
        supported_mods = {"BPSK", "QPSK", "16QAM", "64QAM"}  # Pre-reserve structures for QAM validation
        self.modulations = []
        for mod in raw_mods:
            mod_upper = str(mod).upper()
            if mod_upper not in supported_mods:
                raise ValueError(f"Modulation {mod} not supported. Supported modulations: {supported_mods}")
            # Check V1 limitation
            if mod_upper in {"16QAM", "64QAM"}:
                raise ValueError(
                    f"Modulation '{mod_upper}' is designed for future version roadmap and not implemented in V1."
                )
            self.modulations.append(mod_upper)

        # SNR Range
        snr_raw = self._raw.get("snr_db_range", {})
        if not isinstance(snr_raw, dict):
            raise ValueError("snr_db_range must be a dictionary with 'start', 'stop', and 'step'.")
        
        self.snr_range = SNRRange(
            start=float(snr_raw.get("start", 0.0)),
            stop=float(snr_raw.get("stop", 10.0)),
            step=float(snr_raw.get("step", 2.0)),
        )
        if self.snr_range.step <= 0:
            raise ValueError("SNR range step must be greater than 0.")
        if self.snr_range.start > self.snr_range.stop:
            raise ValueError("SNR start cannot be greater than stop.")

        # Channel Impairments
        imp_raw = self._raw.get("channel_impairments", {})
        cfo = float(imp_raw.get("cfo_hz", 0.0))
        p_noise = float(imp_raw.get("phase_noise_var", 0.0))
        if p_noise < 0.0:
            raise ValueError("phase_noise_var cannot be negative.")
        
        taps = imp_raw.get("multipath_taps", [1.0])
        if not isinstance(taps, list) or not taps:
            raise ValueError("multipath_taps must be a non-empty list of coefficients.")
        try:
            taps = [float(t) for t in taps]
        except ValueError:
            raise ValueError("All multipath_taps coefficients must be real numbers.")

        self.channel_impairments = ChannelImpairments(
            cfo_hz=cfo, phase_noise_var=p_noise, multipath_taps=taps
        )

        # Outputs configuration
        outputs_raw = self._raw.get("outputs", {})
        self.output_dir = str(outputs_raw.get("output_dir", "outputs"))
        self.generate_plots = bool(outputs_raw.get("generate_plots", True))
        self.generate_reports = bool(outputs_raw.get("generate_reports", True))

    @classmethod
    def load_from_json(cls, file_path: str) -> "SimulationConfig":
        """Loads configuration from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format in configuration file: {e}")
        
        return cls(data)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current configuration back to dictionary."""
        return {
            "engine": self.engine,
            "num_bits": self.num_bits,
            "sample_rate": self.sample_rate,
            "sps": self.sps,
            "excess_bw": self.excess_bw,
            "filter_span": self.filter_span,
            "modulations": self.modulations,
            "snr_db_range": {
                "start": self.snr_range.start,
                "stop": self.snr_range.stop,
                "step": self.snr_range.step,
            },
            "channel_impairments": {
                "cfo_hz": self.channel_impairments.cfo_hz,
                "phase_noise_var": self.channel_impairments.phase_noise_var,
                "multipath_taps": self.channel_impairments.multipath_taps,
            },
            "outputs": {
                "output_dir": self.output_dir,
                "generate_plots": self.generate_plots,
                "generate_reports": self.generate_reports,
            },
        }
