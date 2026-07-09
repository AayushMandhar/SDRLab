"""
Main Streamlit Application for SDRLab.
Provides an interactive web-based dashboard on top of the SDRLab simulation backend.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os

# Resolve the project root and add to python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from streamlit_app.utils.sim_runner import run_sdrlab_simulation

# Set wide layout and title
st.set_page_config(
    page_title="SDRLab Wireless Simulation Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling for the engineering tool aesthetics
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #0A2540;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #639FAB;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #008080;
    }
    .metric-lbl {
        font-size: 0.9rem;
        color: #495057;
    }
    </style>
""", unsafe_style_html=True)


def load_file_content(path: Path) -> str:
    """Helper to read file content securely."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    # Sidebar Navigation Page Selector
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Project Info", "About"])

    # Define paths
    outputs_dir = project_root / "outputs"
    csv_path = outputs_dir / "csv" / "sweep_results.csv"
    report_path = outputs_dir / "reports" / "simulation_report.md"
    log_path = outputs_dir / "logs" / "simulation.log"
    plots_dir = outputs_dir / "plots"
    figures_dir = outputs_dir / "figures"

    if page == "Dashboard":
        st.markdown('<div class="main-title">📡 SDRLab Simulation Control Panel</div>', unsafe_style_html=True)
        st.markdown('<div class="sub-title">Interactive Wireless Communication Performance Analyzer</div>', unsafe_style_html=True)
        
        # Sidebar parameters configuration
        st.sidebar.markdown("---")
        st.sidebar.subheader("Configuration Panel")
        
        engine = st.sidebar.selectbox(
            "Simulation Engine",
            ["Auto", "Simulation", "GNU Radio"],
            index=0,
            help="Select the hardware backend. 'Auto' detects if GNU Radio is present and falls back to Native Simulation if not."
        ).lower()
        if engine == "native simulation":
            engine = "simulation"

        modulation = st.sidebar.selectbox(
            "Modulation Scheme",
            ["BPSK", "QPSK"],
            index=1
        )
        
        st.sidebar.markdown("**Eb/N0 Sweep Settings (dB)**")
        snr_start = st.sidebar.slider("SNR Start", min_value=-10.0, max_value=20.0, value=0.0, step=1.0)
        snr_stop = st.sidebar.slider("SNR Stop", min_value=-10.0, max_value=20.0, value=12.0, step=1.0)
        snr_step = st.sidebar.slider("SNR Step", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

        num_bits = st.sidebar.number_input(
            "Simulation Bit Budget",
            min_value=1000,
            max_value=1000000,
            value=40000,
            step=10000,
            help="Total bits to modulate per sweep point."
        )

        sps = st.sidebar.slider("Samples Per Symbol (SPS)", min_value=2, max_value=16, value=4, step=1)
        sample_rate = st.sidebar.number_input("Sample Rate (Hz)", min_value=100000, max_value=10000000, value=1000000, step=100000)
        
        st.sidebar.markdown("**Channel Impairments**")
        cfo_hz = st.sidebar.slider("Carrier Frequency Offset (Hz)", min_value=0.0, max_value=1000.0, value=0.0, step=10.0)
        phase_noise_var = st.sidebar.slider("Phase Noise Variance", min_value=0.0, max_value=0.1, value=0.0, step=0.005, format="%.3f")
        multipath_taps = st.sidebar.text_input("Multipath Taps (comma separated)", value="1.0, 0.2, 0.05")

        generate_plots = st.sidebar.checkbox("Generate Visualization Plots", value=True)
        generate_reports = st.sidebar.checkbox("Generate Markdown Reports", value=True)
        
        st.sidebar.markdown("---")
        
        col_run, col_reset = st.sidebar.columns(2)
        
        run_pressed = col_run.button("🚀 Run Sweep", use_container_width=True)
        reset_pressed = col_reset.button("🔄 Reset Parameters", use_container_width=True)

        if reset_pressed:
            st.rerun()

        # Main Page Configurations Summary Cards
        st.subheader("Current Settings Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-lbl">Target Backend</div><div class="metric-val">{engine.upper()}</div></div>', unsafe_style_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-lbl">Modulation</div><div class="metric-val">{modulation}</div></div>', unsafe_style_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-lbl">SNR Range</div><div class="metric-val">{snr_start}dB to {snr_stop}dB</div></div>', unsafe_style_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-lbl">Bit Budget</div><div class="metric-val">{num_bits:,} bits</div></div>', unsafe_style_html=True)

        st.markdown("---")

        # Run action trigger
        if run_pressed:
            if snr_start > snr_stop:
                st.error("Error: SNR Start cannot be larger than SNR Stop.")
            else:
                with st.spinner("Processing wireless DSP simulation sweep... Please wait."):
                    try:
                        results_df, status_msg = run_sdrlab_simulation(
                            engine=engine,
                            modulation=modulation,
                            snr_start=snr_start,
                            snr_stop=snr_stop,
                            snr_step=snr_step,
                            num_bits=num_bits,
                            sps=sps,
                            sample_rate=sample_rate,
                            cfo_hz=cfo_hz,
                            phase_noise_var=phase_noise_var,
                            multipath_taps=multipath_taps,
                            generate_plots=generate_plots,
                            generate_reports=generate_reports
                        )
                        st.success(status_msg)
                        st.session_state["results_df"] = results_df
                        st.session_state["has_run"] = True
                    except Exception as e:
                        st.exception(e)

        # Display Results Section if run has occurred
        if st.session_state.get("has_run", False):
            results_df = st.session_state["results_df"]
            
            st.header("📊 Simulation Results & Analysis")
            
            # Displays overall KPIs from the sweep
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
            with kpi_col1:
                min_ber = results_df["Empirical_BER"].min()
                st.metric("Min Empirical BER", f"{min_ber:.6f}")
            with kpi_col2:
                max_ber = results_df["Empirical_BER"].max()
                st.metric("Max Empirical BER", f"{max_ber:.6f}")
            with kpi_col3:
                min_evm = results_df["EVM_Percent"].min()
                st.metric("Min EVM (RMS %)", f"{min_evm:.2f}%")
            with kpi_col4:
                max_evm = results_df["EVM_Percent"].max()
                st.metric("Max EVM (RMS %)", f"{max_evm:.2f}%")

            # Result View Tabs
            tab_table, tab_ber_curve, tab_constellation, tab_waveform, tab_report = st.tabs([
                "📋 Data Table", 
                "📈 BER Curve", 
                "🌌 Constellation Diagrams", 
                "〰️ Signal Waveforms & PSD", 
                "📝 Report & Log Summaries"
            ])
            
            with tab_table:
                st.subheader("Performance Sweep Metrics")
                st.dataframe(results_df, use_container_width=True)
                
            with tab_ber_curve:
                st.subheader("BER vs. Eb/N0 Waterfall Curve")
                ber_img = plots_dir / "ber_vs_snr.png"
                if ber_img.exists():
                    st.image(str(ber_img), caption="BER Waterfall curve comparison (Empirical vs. Theoretical AWGN limits)")
                else:
                    st.warning("BER plot file not found. Ensure 'Generate Visualization Plots' checkbox is checked.")
                    
            with tab_constellation:
                st.subheader("Symbol Constellation Comparison (Ideal vs Noisy vs Recovered)")
                # Scan for constellation plots in figures folder
                if figures_dir.exists():
                    fig_files = [f for f in os.listdir(figures_dir) if "constellation" in f and f.endswith(".png")]
                    if fig_files:
                        selected_fig = st.selectbox("Select SNR checkpoint figure to view:", sorted(fig_files))
                        st.image(str(figures_dir / selected_fig), caption=f"Constellation scatter comparison for {selected_fig}")
                    else:
                        st.info("No constellation plots found in outputs directory.")
                else:
                    st.warning("Figures output directory does not exist.")
                    
            with tab_waveform:
                st.subheader("Time-Domain Waveforms & Welch Power Spectrum Density (PSD)")
                # Scan for waveform and PSD files in figures folder
                if figures_dir.exists():
                    wv_files = [f for f in os.listdir(figures_dir) if "waveform" in f and f.endswith(".png")]
                    psd_files = [f for f in os.listdir(figures_dir) if "psd" in f and f.endswith(".png")]
                    
                    col_wv, col_psd = st.columns(2)
                    with col_wv:
                        st.markdown("#### Time Waveforms")
                        if wv_files:
                            selected_wv = st.selectbox("Select Waveform SNR:", sorted(wv_files))
                            st.image(str(figures_dir / selected_wv), caption=f"Waveform snippet for {selected_wv}")
                        else:
                            st.info("No time waveforms found.")
                    with col_psd:
                        st.markdown("#### Welch Power Spectral Density")
                        if psd_files:
                            selected_psd = st.selectbox("Select PSD SNR:", sorted(psd_files))
                            st.image(str(figures_dir / selected_psd), caption=f"PSD spectrum comparison for {selected_psd}")
                        else:
                            st.info("No PSD spectra found.")
                            
            with tab_report:
                col_rep, col_log = st.columns(2)
                with col_rep:
                    st.markdown("#### Compiled Markdown Report Summary")
                    report_content = load_file_content(report_path)
                    if report_content:
                        st.markdown(report_content[:5000] + "\n\n*(Truncated for preview...)*")
                    else:
                        st.info("Markdown report is empty or not generated.")
                with col_log:
                    st.markdown("#### Tail of Simulation Log")
                    log_content = load_file_content(log_path)
                    if log_content:
                        st.code("\n".join(log_content.splitlines()[-50:]), language="text")
                    else:
                        st.info("Simulation log file not found.")

            # Downloads Panel
            st.markdown("---")
            st.subheader("💾 Export & Download Deliverables")
            d_col1, d_col2, d_col3 = st.columns(3)
            
            if csv_path.exists():
                with open(csv_path, "rb") as f:
                    d_col1.download_button(
                        "Download Results CSV",
                        f,
                        file_name="sweep_results.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            if report_path.exists():
                with open(report_path, "rb") as f:
                    d_col2.download_button(
                        "Download Markdown Report",
                        f,
                        file_name="simulation_report.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
            if log_path.exists():
                with open(log_path, "rb") as f:
                    d_col3.download_button(
                        "Download Simulation Log",
                        f,
                        file_name="simulation.log",
                        mime="text/plain",
                        use_container_width=True
                    )

    elif page == "Project Info":
        st.title("📚 SDRLab Project Information")
        
        st.header("1. Core System Architecture")
        st.markdown("""
        SDRLab uses a unified, modular architecture separating configuration, DSP code processing, outputs generation, and dashboard visualization:
        
        *   **Config Manager**: Validates input boundaries (e.g. sample rates, SPS, modulations).
        *   **DSP Engine**:
            *   *Native Engine*: In-memory NumPy operations for modulation, pulse shaping, noise addition, and matched filters.
            *   *GNU Radio Engine*: Programmatic C++ flowgraph linking sources, constellation mapping blocks, and noise channels using C++ bindings.
        *   **Synchronization**: Symbol peak timing alignment based on cross-correlation delay calculations.
        *   **Automated Metrics**: Unified calculations of EVM and BER performance waterfall curves.
        """)
        
        st.header("2. Technology Stack")
        st.markdown("""
        *   **Programming Language**: Python 3.8+
        *   **SDR Engine**: GNU Radio 3.10.x Programmatic API bindings
        *   **Math / Matrix Operations**: NumPy, SciPy (firdes RRC filter generation, erfc calculation)
        *   **Data Serialization**: Pandas, JSON, CSV
        *   **Visualization**: Matplotlib, Streamlit
        """)

        st.header("3. Project Roadmap")
        st.markdown("""
        *   **Version 1.0 (Current)**:
            - Dual-engine core pipeline (Simulation vs GNU Radio).
            - BPSK and QPSK Gray-coded modulators.
            - Channel impairments (CFO, phase noise, fading, AWGN).
            - Interactive Streamlit Dashboard controls.
        *   **Version 1.1 (Planned)**:
            - Interactive Streamlit sweeps comparing Native vs GNU Radio engines side-by-side.
            - Costas Loop carrier tracking integrations.
        *   **Version 1.2 (Planned)**:
            - 16-QAM and 64-QAM modulator plugins.
            - Gardner timing recovery TED loops.
        *   **Version 2.0 (Planned)**:
            - Physical RF hardware integrations (RTL-SDR, USRP sources).
        """)

    elif page == "About":
        st.title("ℹ️ About SDRLab")
        st.markdown("""
        **SDRLab** was built to demonstrate clean Software Engineering concepts (Object-Oriented Programming, Separation of Concerns, plugin registries, and automated test environments) applied directly to the engineering field of Software-Defined Radio.
        
        *   **Author**: Software-Defined Radio Engineering Intern
        *   **License**: MIT License
        *   **GitHub Repository**: [GitHub Sandbox Repository Placeholder]
        
        ### Acknowledgements
        *   **GNU Radio Project**: For providing the excellent, high-performance open-source toolkit.
        *   **Python SciPy Team**: For enabling fast, portable mathematical calculations.
        """)


if __name__ == "__main__":
    main()
