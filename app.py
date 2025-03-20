"""
Main entry point for the NSE Trading Strategies application.
"""

import streamlit as st


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="NSE Trading Strategies",
        page_icon="📈",
        layout="wide",
    )

    st.title("NSE Trading Strategies")
    st.write(
        """
    Welcome to the NSE Trading Strategies application. This app provides various 
    trading strategies for NSE stocks and futures.
    
    Select a strategy from the sidebar to get started.
    """
    )

    st.sidebar.success("Select a strategy above.")

    # Display app information
    st.markdown(
        """
    ## Available Strategies
    
    - **Calendar Spread**: Analyze and backtest calendar spread strategies for NSE futures
    - More strategies coming soon!
    
    ## How to Use
    
    1. Select a strategy from the sidebar
    2. Configure the parameters as needed
    3. View the results and analysis
    """
    )


if __name__ == "__main__":
    main()
