# Changelog

All notable changes to the **SDRLab** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-09

### Added
- **Dual-Engine Core**: Programmatic Simulation Engine (NumPy/SciPy) and GNU Radio Flowgraph Engine with automatic fallback logic.
- **Config-Driven CLI**: Command-line validation interface parsing settings for modulations, samples per symbol, sample rate, filter parameters, and channel profiles.
- **Modulator Plugin Framework**: Modular `BaseModulator` subclassed by `BPSKModulator` and `QPSKModulator` plugins.
- **Transmitter/Receiver Pipelines**: Pulse shaping and matched filtering utilizing custom-generated Root Raised Cosine (RRC) coefficients.
- **Channel Impairments**: Channel models for CFO (carrier frequency offset), phase noise walk, multi-tap fading delays, and noise power calculations.
- **Robust Synchronization**: Cross-correlation synchronization algorithm to align symbols and resolve timing peaks.
- **Visualizer Suite**: Core visualization tools to plot constellations, time-domain signals, Power Spectral Density (Welch method), and BER sweep comparison lines.
- **Automated Reporter**: Generates structured Markdown summaries referencing generated assets and performance tables.
- **Test Suite**: 15 unit and integration tests verifying configurations, DSP routines, metrics math, and controller flows.

### Changed
- Refactored `sdrlab/logger.py` to invoke `handler.close()` when clearing handlers, preventing Windows resource leaks.
- Adjusted RRC matched filter timing recovery thresholds in unit tests to account for physical truncation ISI constraints.
- Switched to `os.path.relpath` inside `sdrlab/reports.py` to support relative links between sibling folders.
