"""
About page view for the SDRLab Streamlit dashboard.
"""

import streamlit as st


def render_about() -> None:
    """
    Renders the About SDRLab details page.
    """
    st.markdown('<div class="main-title">ℹ️ About SDRLab</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Software Engineering paradigms in Software Defined Radio Systems</div>', unsafe_allow_html=True)
    
    st.write(
        "SDRLab was designed to prove that complex, math-intensive domains like digital communication and "
        "baseband DSP can benefit from rigorous Software Engineering principles rather than being limited to "
        "throw-away scripts."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ Software Engineering Principles")
        st.markdown("""
        *   **Separation of Concerns**: Isolated packages manage configurations, logging, baseband DSP calculations, vector captures, visual graphing, and report exporting separately.
        *   **Modular Extensibility**: Adding new modulation formats is as simple as registering new subclasses under the modulator plugin system without modifying main scripts.
        *   **Clean API Boundaries**: Programmatic inputs and outputs decouple the visualization dashboard (Streamlit) from the core signal processing engines, enabling headless execution.
        """)
        
        st.subheader("📐 SDR Engineering Goals")
        st.markdown("""
        *   **Channel Impairments**: Rigorous simulation of physical transmission mediums including phase noise variance, Carrier Frequency Offset (CFO), and multipath delay profiles.
        *   **Ideal Synchronization**: Timing recovery using cross-correlation delay detection allows accurate estimation of symbol alignment under ISI.
        """)
        
    with col2:
        st.subheader("📻 GNU Radio 3.10 Integration")
        st.markdown("""
        *   **C++ Performance**: Chaining native C++ GNU Radio blocks (`blocks.pack_k_bits_bb`, `digital.chunks_to_symbols_bc`, `filter.interp_fir_filter_ccf`) provides high throughput while utilizing dynamic python runtime loading.
        *   **Unified Validation**: Dual-engine architecture guarantees that the custom NumPy/SciPy baseband transmitter and receiver output matched symbols identical to the GNU Radio flowgraph.
        """)
        
        st.subheader("📋 Project Details")
        st.markdown("""
        *   **Author**: Software-Defined Radio Engineering Intern
        *   **Project Sponsor**: Senior GNU Radio Developer & SDR Mentor
        *   **License**: MIT License
        *   **Version**: 1.1 (Streamlit Edition)
        *   **GitHub**: [GitHub Sandbox Repository Placeholder]
        """)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Landing Page", use_container_width=True):
        st.session_state["current_page"] = "Landing"
        st.rerun()
