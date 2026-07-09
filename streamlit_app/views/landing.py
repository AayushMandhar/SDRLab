"""
Landing page view for the SDRLab Streamlit dashboard.
"""

import streamlit as st


def render_landing() -> None:
    """
    Renders the premium dark-themed landing page.
    """
    # Centered radar/satellite dish icon using styling
    st.markdown('<div class="landing-logo">📡</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-title">SDRLab</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Software Defined Radio Simulation Framework</div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="landing-intro">
            SDRLab is a modular, configuration-driven software engineering platform designed to simulate, 
            analyze, and compare baseband digital wireless communication systems. By combining Python's 
            scientific computing stack with programmatic GNU Radio bindings, it offers a robust, 
            interactive workbench for evaluating digital modulations, synchronizers, and channel impairments.
        </div>
    """, unsafe_allow_html=True)
    
    # Technology badges
    st.markdown("""
        <div class="landing-badges">
            <span class="landing-badge">🐍 Python 3.8+</span>
            <span class="landing-badge">📻 GNU Radio 3.10+</span>
            <span class="landing-badge">🔢 NumPy</span>
            <span class="landing-badge">🧪 SciPy</span>
            <span class="landing-badge">📊 Pandas</span>
            <span class="landing-badge">📈 Matplotlib</span>
            <span class="landing-badge">🌐 Streamlit</span>
            <span class="landing-badge">🐱 Git</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Large action buttons in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Launch Panel", use_container_width=True, help="Open the simulation dashboard"):
            st.session_state["current_page"] = "Dashboard"
            st.rerun()
            
    with col2:
        if st.button("📚 System Info", use_container_width=True, help="Explore architecture and repository structure"):
            st.session_state["current_page"] = "Project Info"
            st.rerun()
            
    with col3:
        if st.button("ℹ️ About SDRLab", use_container_width=True, help="Learn about the engineering and design principles"):
            st.session_state["current_page"] = "About"
            st.rerun()
            
    with col4:
        st.link_button(
            "💻 GitHub Repo",
            "https://github.com/yourusername/SDRLab",
            use_container_width=True,
            help="View the source code on GitHub"
        )
