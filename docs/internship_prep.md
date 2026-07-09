# SDRLab: Internship & Technical Interview Preparation Guide

This guide is prepared to help you present the **SDRLab** project in professional settings, such as resumes, job interviews, viva sessions, and portfolio reviews.

---

## 1. Resume Project Description

**SDRLab: A Python-Based Configurable Wireless Communication Simulation Framework**
* Developed a modular, configuration-driven simulation platform in Python utilizing NumPy, SciPy, Pandas, and Matplotlib alongside GNU Radio programmatically to simulate and evaluate digital baseband communication systems.
* Implemented a dual-execution engine (Native NumPy DSP vs. GNU Radio bindings) to guarantee cross-environment portability, facilitating headless testing and automated CI verification in environments lacking native GNU Radio.
* Designed an extensible plugin architecture for digital modulators (BPSK/QPSK) enabling higher-order formats (16-QAM/64-QAM) to be introduced dynamically without code modifications.

---

## 2. Professional Resume Experience Bullets

* Engineered a wireless communication simulation framework supporting dual execution modes (pure Python DSP & programmatic GNU Radio C++ bindings) to ensure seamless portability across Linux and Windows environments.
* Designed a plugin-based modulation framework allowing higher-order modulation formats (16-QAM/64-QAM) to be registered dynamically without altering downstream synchronization or metrics layers.
* Formulated mathematical metrics (empirical vs. theoretical BER, EVM, and power-to-SNR conversion) to validate simulation bounds against AWGN limits.
* Built a cross-correlation-based alignment algorithm that dynamically calculates RRC group delay offsets, resolving timing peak synchronization for both engines.
* Authored an automated markdown reporting engine that compiles CSV sweep data and matplotlib visual assets (constellations, PSD, eye-waveforms) into structured performance summaries.
* Established a comprehensive unit and integration test suite (15 tests, 100% pass) and eliminated Windows-specific resource lock warnings by designing a thread-safe logger shutdown handler.

---

## 3. STAR Interview Method Walkthrough

When asked to describe a technical challenge or project, use the **STAR (Situation, Task, Action, Result)** structure:

* **S (Situation)**: During my software engineering work on wireless simulations, we needed a platform to evaluate digital communication links using GNU Radio. However, GNU Radio has a heavy C++ installation footprint and is notoriously difficult to install in virtual testing systems, headless clouds, and Windows environments, blocking standard developers from running tests.
* **T (Task)**: I was tasked with designing a modular simulation framework that can use GNU Radio's C++ DSP blocks when available, but fall back to a pure-Python DSP simulation engine in standard IDEs or CI pipelines, while keeping metrics and data analysis perfectly unified.
* **A (Action)**: I developed **SDRLab**. I structured the codebase with a unified `SimulationController` and isolated transmitter/receiver architectures. I created a plugin modulator system (BaseModulator -> BPSK/QPSK) to ensure new formats could plug in. I programmatically wrapped GNU Radio blocks (`gr.top_block`) to extract raw samples into NumPy vectors. I resolved timing differences between the Python and C++ RRC filters by designing a cross-correlation alignment block that calculates group delay offsets on-the-fly. Finally, I resolved resource leaks on Windows by structuring a proper teardown sequence for the logging handlers.
* **R (Result)**: The system succeeded with a 100% unit test pass rate. Developers can now run full BER sweeps from any standard command line using the `--engine simulation` flag, while SDR engineers can run the identical configuration with the `--engine gnuradio` flag. Output metrics and graphs are generated automatically into organized directories, reducing validation overhead from hours to a single CLI command.

---

## 4. Technical Interview Questions & Answers

### Q: Why do we use Root Raised Cosine (RRC) filtering at both the transmitter and receiver?
**A**: We use RRC filters as a matched filter pair. Convolving the transmit signal with an RRC filter and then convolving the received signal with a matching RRC filter results in a Raised Cosine (RC) pulse response. The RC response satisfies the **Nyquist ISI Criterion**, which means at the exact symbol sampling instances, the inter-symbol interference is exactly zero. Placing half the filter shape in the transmitter and the other half in the receiver maximizes the Signal-to-Noise Ratio (SNR) in the presence of Additive White Gaussian Noise (AWGN).

### Q: What is EVM and how is it calculated in your metrics module?
**A**: **Error Vector Magnitude (EVM)** is a measure of the quality of demodulated constellation symbols. It represents the difference (error vector) between the received, synchronized symbol $S_{\text{rx}}$ and the ideal reference symbol $S_{\text{tx}}$.
$$\text{EVM}_{\text{RMS}} = \sqrt{\frac{\frac{1}{N}\sum |S_{\text{rx}} - S_{\text{tx}}|^2}{P_{\text{avg}}}} \times 100\%$$
where $P_{\text{avg}}$ is the average power of the ideal constellation points. In our code, we measure EVM as an RMS percentage. A higher SNR yields smaller error vectors and therefore a lower EVM percentage.

### Q: How does your timing synchronization work if you don't implement a Gardner loop in Version 1?
**A**: Because our channel is simulated in a synchronous environment without arbitrary fractional timing drift, the symbol timing offset is stationary and is caused entirely by the group delay of the RRC matched filters (each filter introduces a delay of $\text{span} \cdot \text{sps} / 2$ samples, totaling $\text{span} \cdot \text{sps}$). To make the code robust against any variations (such as when switching between Python and C++ GNU Radio filters), we compute the **cross-correlation** between the matched filtered received samples and the ideal transmitted symbols upsampled by SPS. The peak of the cross-correlation magnitude indicates the exact group delay offset in samples. We then down-sample the filtered waveform starting at this peak index, taking every SPS-th sample, resulting in perfectly aligned symbols.

---

## 5. Viva Questions & Answers

### Q: What is the purpose of the `__init__.py` files in your project?
**A**: They mark directories as Python packages. This allows modules in the subfolders to be imported using standard package paths (e.g. `from sdrlab.dsp.modulator import ModulatorFactory`). It also serves as initialization space to define package-level variables like `__version__`.

### Q: Why did the unit tests fail on Windows originally, and how did you fix it?
**A**: The test suite failed during cleanup because a test tried to delete the temporary output directory (`outputs_test/`) containing log files. On Windows, a file cannot be deleted if a process still holds an open file handle. In Python's `logging` system, `FileHandler` keeps a file open until closed. I solved this by implementing a classmethod `SDRLabLogger.shutdown()` that iterates over all logger handlers, explicitly calls `handler.close()`, and removes them from the logger. Calling this in the test cleanup released the lock, allowing `shutil.rmtree` to execute successfully.

---

## 6. Software Engineering Discussion Points

* **Configuration-Driven Design**: The CLI loads arguments directly from `config.json`. The `SimulationConfig` class acts as a single source of truth, validating values and types, and preventing runtime crashes by throwing early errors for illegal boundaries.
* **Separation of Concerns**: The visualizer is responsible *only* for generating plot files. The reports module is responsible *only* for writing markdown layout strings. The controller manages the execution flow. This prevents tight coupling and makes the modules easy to reuse.
* **Loose Coupling**: Modulations are accessed via the `ModulatorFactory` interface. If a developer wants to add `QAM16`, they only need to write a class subclassing `BaseModulator` and register it. The rest of the codebase (the controller, the metrics, and the report assembler) remains unchanged.
