"""
KPI Metric Cards component for the SDRLab Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
from typing import Optional


def render_kpi_cards(results_df: Optional[pd.DataFrame] = None, elapsed_time: Optional[float] = None) -> None:
    """
    Renders the KPI card layout at the top of the dashboard.
    
    Args:
        results_df: Optional pandas DataFrame with the simulation sweep metrics.
        elapsed_time: Optional execution time in seconds.
    """
    st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
    
    if results_df is not None and not results_df.empty:
        # Extract metrics
        min_ber = results_df["Empirical_BER"].min()
        theory_ber = results_df["Theoretical_BER"].min()
        min_evm = results_df["EVM_Percent"].min()
        max_snr = results_df["Measured_SNR_dB"].max()
        
        # Grid layout using columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="kpi-card kpi-card-ber">
                    <div class="kpi-lbl">📉 Min Empirical BER</div>
                    <div class="kpi-val">{min_ber:.6f}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="kpi-card kpi-card-theory">
                    <div class="kpi-lbl">📈 Theoretical BER</div>
                    <div class="kpi-val">{theory_ber:.6f}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="kpi-card kpi-card-evm">
                    <div class="kpi-lbl">💫 Min EVM (RMS)</div>
                    <div class="kpi-val">{min_evm:.2f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            time_str = f"{elapsed_time:.2f}s" if elapsed_time is not None else "N/A"
            st.markdown(f"""
                <div class="kpi-card kpi-card-time">
                    <div class="kpi-lbl">⏱️ Execution Time</div>
                    <div class="kpi-val">{time_str}</div>
                </div>
            """, unsafe_allow_html=True)
            
    else:
        # Default placeholder cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                <div class="kpi-card kpi-card-ber">
                    <div class="kpi-lbl">📉 Min Empirical BER</div>
                    <div class="kpi-val">--</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
                <div class="kpi-card kpi-card-theory">
                    <div class="kpi-lbl">📈 Theoretical BER</div>
                    <div class="kpi-val">--</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
                <div class="kpi-card kpi-card-evm">
                    <div class="kpi-lbl">💫 Min EVM (RMS)</div>
                    <div class="kpi-val">--</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown("""
                <div class="kpi-card kpi-card-time">
                    <div class="kpi-lbl">⏱️ Execution Time</div>
                    <div class="kpi-val">--</div>
                </div>
            """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)
