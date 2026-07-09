"""
SDRLab Web Application Entry Point.
Coordinates dashboard layout, page states, and style sheet injection.
"""

import sys
from pathlib import Path
import streamlit as st

# Add the project root to python path to import packages
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.views.landing import render_landing
from streamlit_app.views.info import render_info
from streamlit_app.views.about import render_about
from streamlit_app.views.dashboard import render_dashboard

# Page Configurations
st.set_page_config(
    page_title="SDRLab Premium Simulation Suite",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css(css_file_path: Path) -> None:
    """Injects custom CSS styles into the dashboard page layout."""
    if css_file_path.exists():
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    # Load custom styles
    css_path = project_root / "streamlit_app" / "styles" / "custom.css"
    load_css(css_path)

    # Initialize page state
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Landing"

    # Sidebar Navigation Page Override
    st.sidebar.title("SDRLab Navigation")
    selected_nav = st.sidebar.radio(
        "Page Selector", 
        ["Landing Page", "Simulation Control Panel", "Project Information", "About Framework"],
        index=0 if st.session_state["current_page"] == "Landing" 
              else 1 if st.session_state["current_page"] == "Dashboard"
              else 2 if st.session_state["current_page"] == "Project Info"
              else 3
    )

    # Synchronize selectbox nav clicks to the session state
    if selected_nav == "Landing Page":
        st.session_state["current_page"] = "Landing"
    elif selected_nav == "Simulation Control Panel":
        st.session_state["current_page"] = "Dashboard"
    elif selected_nav == "Project Information":
        st.session_state["current_page"] = "Project Info"
    elif selected_nav == "About Framework":
        st.session_state["current_page"] = "About"

    # Render appropriate page based on state
    current_page = st.session_state["current_page"]

    if current_page == "Landing":
        render_landing()
    elif current_page == "Dashboard":
        # Renders the sidebar inputs
        config, run_pressed, reset_pressed = render_sidebar()
        if reset_pressed:
            st.session_state["has_run"] = False
            st.session_state["results_df"] = None
            st.session_state["elapsed_time"] = None
            st.rerun()
        # Renders the dashboard page body
        render_dashboard(project_root, config, run_pressed)
    elif current_page == "Project Info":
        render_info()
    elif current_page == "About":
        render_about()

    # Footer
    st.markdown("""
        <div class="dashboard-footer">
            SDRLab — Software Defined Radio Simulation & Engineering Analysis Framework<br>
            Python • GNU Radio • Streamlit | <span class="footer-highlight">Version 1.1</span>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
