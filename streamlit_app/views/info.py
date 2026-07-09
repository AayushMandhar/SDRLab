"""
Project Information page view for the SDRLab Streamlit dashboard.
"""

import streamlit as st


def render_info() -> None:
    """
    Renders the system architecture and repository information.
    """
    st.markdown('<div class="main-title">📚 Project Information</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">System Architecture, Technology Stack, and Execution Workflow</div>', unsafe_allow_html=True)
    
    tab_arch, tab_stack, tab_repo, tab_roadmap = st.tabs([
        "🏗️ System Architecture",
        "🛠️ Technology Stack",
        "📂 Repository Structure",
        "🗺️ Roadmap & Features"
    ])
    
    with tab_arch:
        st.subheader("Unified Execution Flowgraph")
        st.write("Below is the structural flow from config parsing to execution engine, metrics calculation, and reports outputs:")
        
        # Mermaid rendering in Streamlit
        st.components.v1.html(
            """
            <pre class="mermaid" style="background:transparent; border:none; margin:0; padding:0;">
            flowchart TD
                config[config.json] --> CLI[run_simulation.py CLI]
                CLI --> Controller[Simulation Controller]
                
                subgraph Execution Engines
                    Controller -->|Run Engine Mode| EngineDecide{Engine Selection}
                    EngineDecide -->|Simulation| NativeEngine[Native DSP Engine]
                    EngineDecide -->|GNU Radio| GREngine[GNU Radio Engine]
                end
            
                subgraph Native DSP Engine Pipeline
                    NativeEngine --> Tx[Transmitter: Bits -> Symbols -> RRC]
                    Tx --> Channel[Channel: CFO + Phase Noise + Fading + AWGN]
                    Channel --> Rx[Receiver: Matched RRC -> Timing Sync -> Demap]
                end
            
                subgraph GNU Radio Engine Flowgraph
                    GREngine --> GR_Src[vector_source_b]
                    GR_Src --> GR_Mod[pack_k_bits + chunks_to_symbols]
                    GR_Mod --> GR_Pulse[interp_fir_filter RRC]
                    GR_Pulse --> GR_Chan[channel_model]
                    GR_Chan --> GR_Filter[fir_filter_ccf RRC]
                    GR_Filter --> GR_Sinks[vector_sinks]
                end
            
                Rx --> Metrics[Metrics Engine: BER + EVM + SNR]
                GR_Sinks -->|Correlation Alignment| Rx
                Metrics --> Visualizer[Visualizer: Constellations, PSD, FFT, Waveforms]
                Visualizer --> Reports[Simulation Reporter]
                Reports --> Output[outputs/ folder]
            </pre>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({ startOnLoad: true, theme: 'dark' });
            </script>
            """,
            height=650,
            scrolling=True
        )
        
    with tab_stack:
        st.subheader("Framework Technical Specifications")
        st.markdown("""
        The technology stack is divided into three key layers:
        
        *   **User Interface Layer**:
            *   **Streamlit**: Web-based interactive dashboard panel.
            *   **Matplotlib**: Custom, high-resolution baseband plotting.
            *   **Plotly**: Interactive BER waterfall and EVM charts.
            
        *   **DSP Execution Layer**:
            *   **GNU Radio (3.10.x)**: High-speed, C++ compiled core modulation and filtering blocks.
            *   **SciPy**: Timing matched filtering, theoretical erfc boundary calculations, and signal utilities.
            *   **NumPy**: Portable matrix, baseband CFO, phase noise, and array calculations.
            
        *   **Orchestration & Data Layer**:
            *   **Pandas**: Tabulation of empirical vs theoretical KPIs.
            *   **JSON**: Scheme validations and parameter serialization.
        """)
        
    with tab_repo:
        st.subheader("Repository Structure Directory Tree")
        st.code(
            """
SDRLab/
│
├── README.md                      # Project manual and architectural guide
├── LICENSE                        # MIT License
├── requirements.txt               # Declared package dependencies
├── config.json                    # Default simulation configuration file
├── run_simulation.py              # CLI controller entry script
│
├── sdrlab/                        # Core Library Package
│   ├── config.py                  # SimulationConfig validation manager
│   ├── logger.py                  # Structured logger with file-lock release handlers
│   ├── controller.py              # Sweep orchestrator & cross-correlation sync
│   ├── metrics.py                 # Empirical/Theoretical BER, EVM, SNR calculators
│   ├── visualizer.py              # Plotting utilities (constellations, PSD, BER)
│   ├── reports.py                 # Markdown performance report compiler
│   │
│   ├── dsp/                       # Pure Python/NumPy DSP Subpackage
│   │   ├── modulator.py           # Extensible Modulator Plugins (BPSK/QPSK)
│   │   ├── transmitter.py         # Bit generation, upsampling, RRC pulse shaping
│   │   ├── channel.py             # CFO, phase noise, multi-tap fading, AWGN channels
│   │   ├── synchronization.py     # Base interfaces for carrier/timing sync, Ideal Sync
│   │   └── receiver.py            # Matched filter, timing peak slicing, demapping
│   │
│   └── gnuradio/                  # GNU Radio Subpackage
│       └── flowgraph.py           # Programmatic gr.top_block assembly
│
├── streamlit_app/                 # Streamlit Web Frontend Package
│   ├── app.py                     # Main dashboard UI entry point
│   ├── components/                # Modular UI widgets (sidebar components)
│   ├── pages/                     # Section-based pages rendering functions
│   ├── utils/                     # Dashboard simulation runner utilities
│   └── styles/                    # Custom CSS layout styling rules
│
├── tests/                         # Unit & Integration Test Suite
│   └── test_dsp.py                # Modulator, filter energy, and pipeline recovery tests
            """,
            language="text"
        )
        
    with tab_roadmap:
        st.subheader("Milestones & Planned Features")
        st.markdown("""
        *   **Version 1.0 (Stable)**:
            - Dual-engine core pipeline (Simulation vs GNU Radio).
            - BPSK and QPSK Gray-coded modulators.
            - Channel impairments (CFO, phase noise, fading, AWGN).
            - Programmatic C++ block chaining in GNU Radio.
            
        *   **Version 1.1 (Current)**:
            - Premium, dark-themed Streamlit dashboard with custom CSS.
            - Stepper-style multi-stage execution progress bar.
            - Interactive Plotly-rendered BER waterfall curves.
            - Unified workspace and Desktop copy configurations.
            
        *   **Version 1.2 (Planned)**:
            - Phase tracking loops (Costas Loop carrier synchronizer).
            - 16-QAM and 64-QAM modulator plugins.
            - Gardner timing recovery TED loops.
            
        *   **Version 2.0 (Planned)**:
            - Physical RF hardware integrations (RTL-SDR, USRP sources).
        """)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Landing Page", use_container_width=True):
        st.session_state["current_page"] = "Landing"
        st.rerun()
