import streamlit as st
import os
from PIL import Image
import base64

# Set page config
st.set_page_config(
    page_title="TE Connectivity Data Platform",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for landing page
st.markdown("""
<style>
    /* Global styles */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333;
    }
    
    /* Header styles */
    .header-container {
        display: flex;
        align-items: center;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
        margin-bottom: 2rem;
    }
    
    .title-section {
        margin-left: 1rem;
    }
    
    .main-title {
        color: #FF8200;
        font-weight: 900;
        font-size: 5.5rem;
        margin: 0;
        line-height: 1.2;
    }
    
    .subtitle {
        color: #555;
        font-size: 1.1rem;
        margin-top: 0.3rem;
    }
    
    /* Card styles */
    .cards-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        margin-top: 2rem;
    }
    
    .card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 1.5rem;
        width: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        height: 200px;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    .card h3 {
        color: #FF8200;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .card p {
        color: #666;
        font-size: 0.9rem;
    }
    
    .card-icon {
        position: absolute;
        bottom: 1rem;
        right: 1rem;
        font-size: 3rem;
        opacity: 0.1;
        color: #FF8200;
    }
    
    .card-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background-color: #e0e0e0;
        color: #666;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    
    .card.active {
        border: 2px solid #FF8200;
    }
    
    .card.active .card-badge {
        background-color: #FF8200;
        color: white;
    }
    
    .card.disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
    
    .card.disabled:hover {
        transform: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Animation keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(255, 130, 0, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 130, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 130, 0, 0); }
    }
    
    .animate-fadeIn {
        animation: fadeIn 0.8s ease forwards;
    }
    
    .card.active {
        animation: pulseGlow 2s infinite;
    }
    
    /* Welcome banner */
    .welcome-banner {
        background: linear-gradient(135deg, #FF8200 0%, #FFA500 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease;
    }
    
    .welcome-banner h1 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .welcome-banner p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Footer */
    .footer {
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(49, 51, 63, 0.2);
        text-align: center;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Header with TE Connectivity logo
logo_path = "logo.png"
if os.path.exists(logo_path):
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(logo_path, width=150)
    with col2:
        st.markdown('<div class="title-section"><h1 class="main-title">Cost Spark</h1></div>', unsafe_allow_html=True)
else:
    st.error("Logo not found. Please ensure 'logo.png' exists.")

# Welcome banner with animation
st.markdown('''
<div class="welcome-banner">
    <h1>Welcome to TE Connectivity Data Platform</h1>
    <p>Empower your data journey with our comprehensive suite of analytics tools. Gain insights, build models, and drive business decisions with data-driven intelligence.</p>
</div>
''', unsafe_allow_html=True)

# Create option cards with different animation delays
st.markdown('<div class="cards-container">', unsafe_allow_html=True)

# 4 Columns for the cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Instead of a separate button, make the entire card clickable
    eda_card_html = '''
    <div class="card active animate-fadeIn" style="animation-delay: 0.1s; cursor: pointer;" id="eda_card">
        <h3>EDA</h3>
        <p>Exploratory Data Analysis tools for data discovery and cost estimation.</p>
        <div class="card-badge">AVAILABLE</div>
        <div class="card-icon">📊</div>
    </div>
    '''
    st.markdown(eda_card_html, unsafe_allow_html=True)
    
    # Hidden button that will be triggered by JavaScript
    eda_button = st.button("Navigate to Calculator", key="eda_button", help="Navigate to Databricks Cloud Cost Calculator")
    # Hide the button with CSS
    st.markdown("""
    <style>
    div[data-testid="stButton"] {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if eda_button:
        st.switch_page("pages/calculator.py")
    
    # JavaScript to make the card clickable
    st.markdown("""
    <script>
        // Add click event to the EDA card
        document.addEventListener('DOMContentLoaded', function() {
            const edaCard = document.getElementById('eda_card');
            const hiddenButton = document.querySelector('[data-testid="baseButton-undefined"]');
            
            if (edaCard && hiddenButton) {
                edaCard.addEventListener('click', function() {
                    hiddenButton.click();
                });
            }
        });
    </script>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('''
    <div class="card disabled animate-fadeIn" style="animation-delay: 0.3s;">
        <h3>Self Service</h3>
        <p>Build and manage your own data pipelines and visualizations.</p>
        <div class="card-badge">COMING SOON</div>
        <div class="card-icon">🔧</div>
    </div>
    ''', unsafe_allow_html=True)

with col3:
    st.markdown('''
    <div class="card disabled animate-fadeIn" style="animation-delay: 0.5s;">
        <h3>Data Science</h3>
        <p>Leverage machine learning and AI for predictive analytics.</p>
        <div class="card-badge">COMING SOON</div>
        <div class="card-icon">🧪</div>
    </div>
    ''', unsafe_allow_html=True)

with col4:
    st.markdown('''
    <div class="card disabled animate-fadeIn" style="animation-delay: 0.7s;">
        <h3>Sandbox</h3>
        <p>Experiment with new data tools in an isolated environment.</p>
        <div class="card-badge">COMING SOON</div>
        <div class="card-icon">🏝️</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Interactive element - Navigation instruction
st.markdown("""
<div style="text-align: center; margin-top: 3rem; animation: fadeIn 1.5s ease;">
    <p style="font-size: 1.2rem; color: #FF8200;">👆 Click the <strong>EDA card</strong> to access the Databricks Cloud Cost Calculator</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown('''
<div class="footer">
    <p>© 2025 TE Connectivity Ltd. All Rights Reserved. | Data Platform v1.0.0</p>
</div>
''', unsafe_allow_html=True)