"""
Sidebar UI component for the SDRLab Streamlit dashboard.
"""

import streamlit as st
from typing import Dict, Any, Tuple


def render_sidebar() -> Tuple[Dict[str, Any], bool, bool]:
    """
    Renders the sidebar navigation and configuration panels.
    
    Returns:
        Tuple[Dict[str, Any], bool, bool]: Config dictionary, run trigger, reset trigger.
    """
    st.sidebar.title("📡 SDRLab Configuration")
    
    # 1. Simulation Engine and Parameters
    with st.sidebar.expander("⚙️ Simulation Settings", expanded=True):
        engine = st.selectbox(
            "Execution Engine",
            ["Auto", "Simulation", "GNU Radio"],
            index=0,
            help="Select the hardware backend. 'Auto' detects if GNU Radio is present and falls back to Native Simulation if not."
        ).lower()
        
        # Engine translation logic
        if engine == "native simulation":
            engine = "simulation"
        elif engine == "gnu radio":
            engine = "gnuradio"
            
        num_bits = st.number_input(
            "Bit Budget",
            min_value=1000,
            max_value=1000000,
            value=40000,
            step=10000,
            help="Total bits to modulate and process per sweep step."
        )
        
    # 2. Signal Parameters
    with st.sidebar.expander("📶 Signal Settings", expanded=True):
        modulation = st.selectbox(
            "Modulation Scheme",
            ["BPSK", "QPSK"],
            index=1
        )
        sps = st.slider("Samples Per Symbol (SPS)", min_value=2, max_value=16, value=4, step=1)
        sample_rate = st.number_input(
            "Sample Rate (Hz)",
            min_value=100000,
            max_value=10000000,
            value=1000000,
            step=100000
        )
        
    # 3. Channel Impairments
    with st.sidebar.expander("🌪️ Channel Impairments", expanded=False):
        cfo_hz = st.slider("Carrier Frequency Offset (Hz)", min_value=0.0, max_value=1000.0, value=0.0, step=10.0)
        phase_noise_var = st.slider("Phase Noise Variance", min_value=0.0, max_value=0.1, value=0.0, step=0.005, format="%.3f")
        multipath_taps = st.text_input("Multipath Taps (comma separated)", value="1.0, 0.2, 0.05")
        
    # 4. Sweep Parameters
    with st.sidebar.expander("📊 Sweep Range (Eb/N0)", expanded=True):
        snr_start = st.slider("SNR Start (dB)", min_value=-10.0, max_value=20.0, value=0.0, step=1.0)
        snr_stop = st.slider("SNR Stop (dB)", min_value=-10.0, max_value=20.0, value=12.0, step=1.0)
        snr_step = st.slider("SNR Step (dB)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

    # 5. Output configurations
    with st.sidebar.expander("📂 Output Settings", expanded=False):
        generate_plots = st.checkbox("Generate Plots", value=True)
        generate_reports = st.checkbox("Generate Reports", value=True)

    st.sidebar.markdown("---")
    
    col_run, col_reset = st.sidebar.columns(2)
    run_pressed = col_run.button("🚀 Run Sweep", use_container_width=True)
    reset_pressed = col_reset.button("🔄 Reset", use_container_width=True)
    
    config = {
        "engine": engine,
        "modulation": modulation,
        "num_bits": num_bits,
        "sps": sps,
        "sample_rate": sample_rate,
        "cfo_hz": cfo_hz,
        "phase_noise_var": phase_noise_var,
        "multipath_taps": multipath_taps,
        "snr_start": snr_start,
        "snr_stop": snr_stop,
        "snr_step": snr_step,
        "generate_plots": generate_plots,
        "generate_reports": generate_reports
    }
    
    return config, run_pressed, reset_pressed
