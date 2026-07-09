"""
Multi-stage progress stepper component for the SDRLab Streamlit dashboard.
"""

import streamlit as st
from typing import List


def render_stepper(current_stage_idx: int) -> str:
    """
    Constructs the custom HTML multi-stage progress indicator.
    
    Args:
        current_stage_idx: Index of the current active stage.
        
    Returns:
        str: HTML representation of the stepper.
    """
    stages = [
        ("⚙️", "Loading Configuration"),
        ("📡", "Initializing DSP Engine"),
        ("⚡", "Generating Symbols"),
        ("🌊", "Running Baseband Channel Simulation"),
        ("📈", "Calculating BER & EVM Metrics"),
        ("🎨", "Generating Matplotlib Visualizations"),
        ("📝", "Compiling Markdown Reports"),
        ("✅", "Completed")
    ]
    
    html = '<div class="stepper-container">'
    html += '<h4>Simulation Execution Pipeline</h4>'
    
    for idx, (icon, label) in enumerate(stages):
        if idx < current_stage_idx:
            status_class = "completed"
            icon_status = "🟢"
        elif idx == current_stage_idx:
            status_class = "active"
            icon_status = "🔵"
        else:
            status_class = "pending"
            icon_status = "⚪"
            
        html += f"""
            <div class="stepper-stage {status_class}">
                <span class="stepper-icon">{icon_status}</span>
                <span class="stepper-label">{icon} {label}</span>
            </div>
        """
        
    html += '</div>'
    return html
