"""
Dashboard main view for the SDRLab Streamlit dashboard.
Provides unconditional tabs rendering with professional placeholders,
robust CSV column auto-mapping, and interactive Plotly curves.
"""

import os
import time
import re
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from streamlit_app.components.kpi_cards import render_kpi_cards
from streamlit_app.components.progress_stepper import render_stepper
from streamlit_app.utils.sim_runner import run_sdrlab_simulation
from sdrlab.logger import SDRLabLogger

logger = SDRLabLogger.get_logger()


def load_file_content(path: Path) -> str:
    """Helper to read file content securely."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read file {path}: {e}")
    return ""


def embed_markdown_images(markdown_text: str, outputs_dir: Path) -> str:
    """
    Parses markdown image tags and replaces relative paths (e.g. ../figures/...)
    with base64 data URIs so Streamlit renders them natively without broken links.
    """
    pattern = r'!\[(.*?)\]\((.*?)\)'
    
    def replace_match(match):
        alt = match.group(1)
        url = match.group(2)
        
        # Clean relative reference path
        url_clean = url.replace("../", "")
        img_path = (outputs_dir / url_clean).resolve()
        
        if img_path.exists() and img_path.is_file():
            try:
                with open(img_path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                return f"![{alt}](data:image/png;base64,{encoded})"
            except Exception as e:
                logger.warning(f"Error base64 encoding image {img_path}: {e}")
                
        return f"![{alt}]({url})"
        
    return re.sub(pattern, replace_match, markdown_text)


def map_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps varying CSV column names to the standard names used by the dashboard
    to prevent KeyError exceptions when loading external files.
    
    Args:
        df: Input pandas DataFrame.
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with standard columns.
    """
    mapping = {
        # Eb/N0 mappings
        "EbN0_dB": "Eb_N0_dB",
        "EbN0": "Eb_N0_dB",
        "Eb/N0": "Eb_N0_dB",
        "Eb/N0_dB": "Eb_N0_dB",
        # Empirical BER mappings
        "Empirical BER": "Empirical_BER",
        "BER": "Empirical_BER",
        "Empirical_BER": "Empirical_BER",
        # Theoretical BER mappings
        "Theoretical BER": "Theoretical_BER",
        "Theoretical_BER": "Theoretical_BER",
        # EVM mappings
        "EVM": "EVM_Percent",
        "EVM %": "EVM_Percent",
        "EVM_RMS": "EVM_Percent",
        # Measured SNR mappings
        "SNR": "Measured_SNR_dB",
        "SNR_dB": "Measured_SNR_dB",
        "Measured SNR": "Measured_SNR_dB",
        # Power mappings
        "Signal Power": "Signal_Power_W",
        "Signal_Power": "Signal_Power_W",
        "Noise Power": "Noise_Power_W",
        "Noise_Power": "Noise_Power_W",
    }
    
    rename_dict = {}
    for col in df.columns:
        col_cleaned = str(col).strip()
        if col_cleaned in mapping:
            rename_dict[col] = mapping[col_cleaned]
        else:
            # Try case-insensitive matching
            for key, val in mapping.items():
                if col_cleaned.lower() == key.lower():
                    rename_dict[col] = val
                    break
                    
    df = df.rename(columns=rename_dict)
    
    # Guarantee critical columns exist with fallback defaults to prevent rendering crashes
    required = ["Modulation", "Eb_N0_dB", "Empirical_BER", "Theoretical_BER", "EVM_Percent", "Measured_SNR_dB"]
    for col in required:
        if col not in df.columns:
            if col == "Modulation":
                df[col] = "QPSK"
            else:
                df[col] = 0.0
                
    return df


def render_dashboard(project_root: Path, config: dict, run_pressed: bool) -> None:
    """
    Renders the main simulation dashboard, handles progress triggers,
    and displays tabbed results and Plotly visualization charts.
    """
    st.markdown('<div class="main-title">📡 Simulation Workbench</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">RF & Software Engineering Digital Communication Analysis Suite</div>', unsafe_allow_html=True)

    # Define paths
    outputs_dir = project_root / "outputs"
    csv_path = outputs_dir / "csv" / "sweep_results.csv"
    report_path = outputs_dir / "reports" / "simulation_report.md"
    log_path = outputs_dir / "logs" / "simulation.log"
    plots_dir = outputs_dir / "plots"
    figures_dir = outputs_dir / "figures"

    # Glassmorphism configuration summary card
    st.markdown(f"""
        <div class="config-summary-card">
            <h4>⚙️ Configuration Summary</h4>
            <strong>Engine:</strong> {config["engine"].upper()} | 
            <strong>Modulation:</strong> {config["modulation"]} | 
            <strong>Bit Budget:</strong> {config["num_bits"]:,} bits | 
            <strong>SPS:</strong> {config["sps"]} | 
            <strong>Sample Rate:</strong> {config["sample_rate"]:,} Hz | 
            <strong>Sweep Range:</strong> {config["snr_start"]}dB to {config["snr_stop"]}dB (step {config["snr_step"]}dB)
        </div>
    """, unsafe_allow_html=True)

    # Auto-load previous session results on startup if session state is empty
    if st.session_state.get("results_df") is None and csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            df = map_dataframe_columns(df)
            st.session_state["results_df"] = df
            st.session_state["has_run"] = True
            logger.info("Successfully recovered last simulation run dataset.")
        except Exception as e:
            logger.warning(f"Could not restore previous session CSV: {e}")

    # 1. Trigger Simulation run and stepper
    if run_pressed:
        if config["snr_start"] > config["snr_stop"]:
            st.error("Error: SNR Start cannot be larger than SNR Stop.")
        else:
            stepper_placeholder = st.empty()
            
            try:
                # Stage 0: Loading Configuration
                stepper_placeholder.markdown(render_stepper(0), unsafe_allow_html=True)
                time.sleep(0.2)
                
                # Stage 1: Initializing DSP Engine
                stepper_placeholder.markdown(render_stepper(1), unsafe_allow_html=True)
                time.sleep(0.2)
                
                # Stage 2: Generating Symbols
                stepper_placeholder.markdown(render_stepper(2), unsafe_allow_html=True)
                time.sleep(0.2)
                
                # Stage 3: Running Baseband Channel Simulation
                stepper_placeholder.markdown(render_stepper(3), unsafe_allow_html=True)
                
                start_time = time.time()
                results_df, status_msg = run_sdrlab_simulation(
                    engine=config["engine"],
                    modulation=config["modulation"],
                    snr_start=config["snr_start"],
                    snr_stop=config["snr_stop"],
                    snr_step=config["snr_step"],
                    num_bits=config["num_bits"],
                    sps=config["sps"],
                    sample_rate=config["sample_rate"],
                    cfo_hz=config["cfo_hz"],
                    phase_noise_var=config["phase_noise_var"],
                    multipath_taps=config["multipath_taps"],
                    generate_plots=config["generate_plots"],
                    generate_reports=config["generate_reports"]
                )
                elapsed_time = time.time() - start_time
                
                # Stage 4: Calculating BER & EVM Metrics
                stepper_placeholder.markdown(render_stepper(4), unsafe_allow_html=True)
                time.sleep(0.15)
                
                # Stage 5: Generating Matplotlib Visualizations
                stepper_placeholder.markdown(render_stepper(5), unsafe_allow_html=True)
                time.sleep(0.15)
                
                # Stage 6: Compiling Markdown Reports
                stepper_placeholder.markdown(render_stepper(6), unsafe_allow_html=True)
                time.sleep(0.15)
                
                # Stage 7: Completed
                stepper_placeholder.markdown(render_stepper(7), unsafe_allow_html=True)
                time.sleep(0.25)
                
                # Clear Stepper UI
                stepper_placeholder.empty()
                
                st.success(status_msg)
                
                # Map column names to prevent KeyError
                results_df = map_dataframe_columns(results_df)
                
                st.session_state["results_df"] = results_df
                st.session_state["elapsed_time"] = elapsed_time
                st.session_state["has_run"] = True
            except Exception as e:
                stepper_placeholder.empty()
                st.markdown(f"""
                    <div style="background-color:rgba(239, 68, 68, 0.1); border:1px solid #EF4444; border-radius:8px; padding:1.2rem; margin:1rem 0;">
                        <h4 style="color:#EF4444; margin-top:0;">⚠️ Baseband Execution Failure</h4>
                        <p>The simulation execution failed. If you attempted to run using the <strong>GNU Radio</strong> engine, 
                        verify that GNU Radio 3.10 is installed and reachable in your environment.</p>
                        <p>Otherwise, switch the <strong>Execution Engine</strong> in the sidebar settings to <strong>Simulation</strong> (Native NumPy fallback) which runs portably without external requirements.</p>
                        <pre style="background-color:rgba(0,0,0,0.2); padding:0.5rem; border-radius:4px; font-size:0.85rem; color:#FCA5A5;">{str(e)}</pre>
                    </div>
                """, unsafe_allow_html=True)
                logger.exception(f"Dashboard sweep run error: {e}")

    # 2. Render KPI cards
    results_df = st.session_state.get("results_df", None)
    elapsed_time = st.session_state.get("elapsed_time", None)
    render_kpi_cards(results_df, elapsed_time)

    # 3. Unconditional tabbed layout display
    st.markdown("---")
    
    tab_metrics, tab_visualizations, tab_reports, tab_downloads, tab_logs = st.tabs([
        "📋 Metrics Table",
        "📊 Interactive Graphs",
        "📝 Markdown Report Preview",
        "💾 Downloads & Configs",
        "📑 Logging Streams"
    ])
    
    # tab_metrics Rendering
    with tab_metrics:
        if results_df is not None:
            st.subheader("Performance Sweep Metrics")
            st.dataframe(results_df, use_container_width=True)
        else:
            st.info("💡 Run a simulation sweep to populate this data table.")
            
    # tab_visualizations Rendering
    with tab_visualizations:
        if results_df is not None:
            st.subheader("Interactive Baseband Graphs")
            col_ber, col_evm = st.columns(2)
            
            with col_ber:
                st.markdown("#### BER vs. Eb/N0 Curve")
                plot_ber = results_df["Empirical_BER"].copy()
                plot_ber[plot_ber == 0.0] = None  # Filter zero values for logarithmic plot rendering
                
                fig_ber = go.Figure()
                fig_ber.add_trace(go.Scatter(
                    x=results_df["Eb_N0_dB"], 
                    y=plot_ber, 
                    mode='lines+markers', 
                    name='Empirical BER',
                    line=dict(color='#00F0FF', width=2.5),
                    marker=dict(size=8)
                ))
                fig_ber.add_trace(go.Scatter(
                    x=results_df["Eb_N0_dB"], 
                    y=results_df["Theoretical_BER"], 
                    mode='lines', 
                    name='Theoretical BER (AWGN)',
                    line=dict(color='#94A3B8', width=1.5, dash='dash')
                ))
                fig_ber.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Eb/N0 (dB)",
                    yaxis_title="Bit Error Rate (BER)",
                    yaxis_type="log",
                    yaxis_range=[-5, 0],
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                st.plotly_chart(fig_ber, use_container_width=True)
                
            with col_evm:
                st.markdown("#### Error Vector Magnitude (EVM) vs. Eb/N0")
                fig_evm = go.Figure()
                fig_evm.add_trace(go.Scatter(
                    x=results_df["Eb_N0_dB"],
                    y=results_df["EVM_Percent"],
                    mode='lines+markers',
                    name='RMS EVM %',
                    line=dict(color='#10B981', width=2.5),
                    marker=dict(size=8)
                ))
                fig_evm.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Eb/N0 (dB)",
                    yaxis_title="EVM (RMS %)",
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                st.plotly_chart(fig_evm, use_container_width=True)

            st.markdown("---")
            st.subheader("Baseband Constellations & Time Waveforms (Static Fallbacks)")
            
            col_const, col_wave = st.columns(2)
            with col_const:
                st.markdown("#### Symbol Constellations")
                if figures_dir.exists():
                    fig_files = [f for f in os.listdir(figures_dir) if "constellation" in f and f.endswith(".png")]
                    if fig_files:
                        selected_fig = st.selectbox("Select Constellation SNR Checkpoint:", sorted(fig_files))
                        st.image(str(figures_dir / selected_fig), use_container_width=True)
                    else:
                        st.info("💡 Run a simulation sweep to generate constellation figures.")
                else:
                    st.info("💡 Run a simulation sweep to generate constellation figures.")
                    
            with col_wave:
                st.markdown("#### Time Signals & PSD Spectra")
                if figures_dir.exists():
                    wv_files = [f for f in os.listdir(figures_dir) if "waveform" in f and f.endswith(".png")]
                    psd_files = [f for f in os.listdir(figures_dir) if "psd" in f and f.endswith(".png")]
                    
                    sub_tab_wv, sub_tab_psd = st.tabs(["〰️ Waveform Snippet", "📶 Welch PSD"])
                    with sub_tab_wv:
                        if wv_files:
                            selected_wv = st.selectbox("Select Waveform SNR Checkpoint:", sorted(wv_files))
                            st.image(str(figures_dir / selected_wv), use_container_width=True)
                        else:
                            st.info("💡 Run a simulation sweep to generate waveform figures.")
                    with sub_tab_psd:
                        if psd_files:
                            selected_psd = st.selectbox("Select PSD SNR Checkpoint:", sorted(psd_files))
                            st.image(str(figures_dir / selected_psd), use_container_width=True)
                        else:
                            st.info("💡 Run a simulation sweep to generate PSD figures.")
                else:
                    st.info("💡 Run a simulation sweep to generate signal waveforms.")
        else:
            st.info("💡 Run a simulation to generate the interactive visualization charts.")
            
    # tab_reports Rendering
    with tab_reports:
        st.subheader("Generated Report Preview")
        if report_path.exists():
            report_content = load_file_content(report_path)
            if report_content:
                # Embed relative image paths as base64 data URIs so Streamlit can render them natively
                embedded_content = embed_markdown_images(report_content, outputs_dir)
                st.markdown(embedded_content, unsafe_allow_html=True)
            else:
                st.info("Markdown report is empty.")
        else:
            st.info("💡 Run a simulation sweep to compile the markdown performance report.")
            
    # tab_downloads Rendering
    with tab_downloads:
        st.subheader("Download Simulation Deliverables")
        if results_df is not None:
            d_col1, d_col2, d_col3 = st.columns(3)
            
            if csv_path.exists():
                with open(csv_path, "rb") as f:
                    d_col1.download_button(
                        "Download CSV Dataset",
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
                        "Download Execution Log",
                        f,
                        file_name="simulation.log",
                        mime="text/plain",
                        use_container_width=True
                    )
        else:
            st.info("💡 Run a simulation sweep to enable downloading the CSV dataset, report, and log files.")
            
    # tab_logs Rendering
    with tab_logs:
        st.subheader("Simulation Tail Log Stream")
        if log_path.exists():
            log_content = load_file_content(log_path)
            if log_content:
                st.code("\n".join(log_content.splitlines()[-60:]), language="text")
            else:
                st.info("Simulation log file is empty.")
        else:
            st.info("💡 No logging files generated yet. Start a simulation run to begin logging.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Landing Page", use_container_width=True):
        st.session_state["current_page"] = "Landing"
        st.rerun()
