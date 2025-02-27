import streamlit as st

from components import run_risk_reward_calculator, run_volume_surge_detector


def main():
    """Main application entry point."""
    st.set_page_config(page_title="Stock Analysis Tool", page_icon="📈", layout="wide")

    # Add title with custom styling
    st.markdown(
        """
        <h1 style='text-align: center; color: #2e7d32;'>
            Stock Analysis Tool
        </h1>
        <p style='text-align: center; color: #666;'>
            Analyze volume surges and calculate trading parameters
        </p>
    """,
        unsafe_allow_html=True,
    )

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["Volume Surge Detector", "Risk Reward Calculator"])

    with tab1:
        run_volume_surge_detector()

    with tab2:
        run_risk_reward_calculator()


if __name__ == "__main__":
    main()
