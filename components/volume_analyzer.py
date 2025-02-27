import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from candle_stick_patterns import get_recent_patterns
from volume_checker import check_volume_surge, get_stocks


def create_volume_chart(ticker, current_volume, avg_volume, previous_volumes):
    """Create a chart comparing current volume to historical volumes and average."""
    # Create volume comparison chart
    volumes = previous_volumes.tolist()
    volumes.append(current_volume)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=len(volumes), freq="B")

    fig = go.Figure()

    # Add volume bars
    marker_colors = ["rgba(55, 128, 191, 0.7)"] * len(previous_volumes)
    marker_colors.append("rgba(50, 171, 96, 0.9)")

    fig.add_trace(
        go.Bar(
            x=dates,
            y=volumes,
            name="Daily Volume",
            marker_color=marker_colors,
        )
    )

    # Add average volume line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[avg_volume] * len(dates),
            name="10-day Average",
            line=dict(color="rgba(255, 0, 0, 0.5)", dash="dash"),
        )
    )

    fig.update_layout(
        title=f"Volume Analysis for {ticker}",
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_white",
        showlegend=True,
    )

    return fig


def run_volume_surge_detector():
    """Run the volume surge detector functionality"""
    # Sidebar for index selection
    st.sidebar.title("Settings")
    index_options = {
        "NIFTY 50": "ind_nifty50list.csv",
        "NIFTY 100": "ind_nifty100list.csv",
        "NIFTY 200": "ind_nifty200list.csv",
    }
    selected_index = st.sidebar.selectbox("Select Index", list(index_options.keys()))

    help_text = "Minimum percentage increase in volume to be considered as surge"
    # Volume surge threshold
    surge_threshold = st.sidebar.slider(
        "Volume Surge Threshold (%)",
        min_value=20,
        max_value=200,
        value=50,
        help=help_text,
    )

    if st.sidebar.button("Scan Stocks", type="primary"):
        with st.spinner("Scanning stocks for volume surges..."):
            tickers = get_stocks(index_options[selected_index])
            surge_results = []

            # Create a progress bar
            progress_bar = st.progress(0)

            for i, ticker in enumerate(tickers):
                ticker_ns = ticker + ".NS"
                result = check_volume_surge(ticker_ns)
                (
                    is_surge,
                    current_volume,
                    avg_volume,
                    previous_volumes,
                    percent_increase,
                ) = result

                if is_surge and percent_increase > surge_threshold:
                    surge_results.append(
                        {
                            "ticker": ticker_ns,
                            "percent_increase": percent_increase,
                            "current_volume": current_volume,
                            "avg_volume": avg_volume,
                            "previous_volumes": previous_volumes,
                        }
                    )

                # Update progress bar
                progress_bar.progress((i + 1) / len(tickers))

            # Sort results by percent increase
            surge_results.sort(key=lambda x: x["percent_increase"], reverse=True)

            display_volume_surge_results(surge_results)


def display_volume_surge_results(surge_results):
    """Display the volume surge results in a nice format."""
    if surge_results:
        msg = f"Found {len(surge_results)} stocks with " "significant volume surge!"
        st.success(msg)

        for result in surge_results:
            title = (
                f"📊 {result['ticker']} - "
                f"{result['percent_increase']:.2f}% Volume Surge"
            )
            with st.expander(title):
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Display volume chart
                    fig = create_volume_chart(
                        result["ticker"],
                        result["current_volume"],
                        result["avg_volume"],
                        result["previous_volumes"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Display metrics
                    volume_diff = result["current_volume"] - result["avg_volume"]
                    volume_delta = f"{volume_diff:,.0f}"

                    st.metric(
                        "Volume Increase",
                        f"{result['percent_increase']:.2f}%",
                        delta=volume_delta,
                    )

                    current_vol = f"{result['current_volume']:,.0f}"
                    st.metric("Current Volume", current_vol)

                    avg_vol = f"{result['avg_volume']:,.0f}"
                    st.metric("10-day Average Volume", avg_vol)

                    # Display candlestick patterns
                    patterns = get_recent_patterns(result["ticker"])
                    if patterns:
                        st.subheader("Recent Patterns")
                        for pattern in patterns:
                            st.markdown(f"• {pattern}")
    else:
        st.warning("No volume surges detected based on current criteria.")
