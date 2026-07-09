# Contributing to SDRLab

We welcome contributions to SDRLab! Whether you are implementing higher-order modulations (e.g., 16-QAM or 64-QAM), developing new synchronization tracking loops (e.g., Costas Loop), or fixing bugs, please follow these guidelines to maintain project quality.

---

## Coding Standards

To maintain standard production quality, please ensure your changes adhere to:
- **Style Guide**: Follow PEP-8 standards.
- **Type Hints**: All function parameters, return values, and module members should include proper type hints.
- **Docstrings**: Provide Google-style docstrings for all classes, methods, and modules.
- **Logging**: Use the centralized logger (`SDRLabLogger.get_logger()`) instead of `print()`.

---

## How to Add a New Modulation Format (Plugin)

SDRLab uses a plugin-based design for modulators. You can add higher-order formats (e.g., `16QAM`) without changing the simulation controller or visualizer:

1. Open [sdrlab/dsp/modulator.py](file:///C:/Users/SLIM%205/.gemini/antigravity/scratch/sdrlab/sdrlab/dsp/modulator.py).
2. Create a new subclass of `BaseModulator`:
   ```python
   class QAM16Modulator(BaseModulator):
       @property
       def name(self) -> str:
           return "16QAM"

       @property
       def bits_per_symbol(self) -> int:
           return 4

       @property
       def constellation(self) -> np.ndarray:
           # Define normalized 16-QAM points
           ...

       def map_bits_to_symbols(self, bits: np.ndarray) -> np.ndarray:
           # Implement mapping logic
           ...

       def demap_symbols_to_bits(self, symbols: np.ndarray) -> np.ndarray:
           # Implement decision demapping logic
           ...
   ```
3. Register the class with the factory at the bottom of the file or in the registry:
   ```python
   ModulatorFactory.register("16QAM", QAM16Modulator)
   ```
4. Update validation schemas in [sdrlab/config.py](file:///C:/Users/SLIM%205/.gemini/antigravity/scratch/sdrlab/sdrlab/config.py) to enable the format in JSON configurations.
5. Write corresponding unit tests inside `tests/test_dsp.py`.

---

## Pull Request Workflow

1. **Fork/Branch**: Create a new feature branch (e.g., `feature/16qam-plugin`).
2. **Run Tests**: Ensure all unit and integration tests are passing before submitting:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```
3. **Verify Output**: Execute the CLI to confirm that output folders (`csv`, `plots`, `figures`, `reports`) generate successfully.
4. **Submit PR**: Open a pull request against the main repository branch.
