import plotly.graph_objects as go
import streamlit as st

from risk_reward_calc import calculate_position_size, calculate_risk_reward_ratio


def run_risk_reward_calculator():
    """Display risk-reward and position size calculator UI"""
    st.header("Risk-Reward & Position Size Calculator")

    st.markdown(
        """
    This calculator helps you determine:
    1. The risk-to-reward ratio for a trade
    2. The appropriate position size based on your risk management rules
    """
    )

    # Create two columns for the two calculators
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk-Reward Ratio Calculator")

        # Input fields for risk-reward calculator
        entry_price = st.number_input(
            "Entry Price", min_value=0.01, value=100.00, step=0.01, format="%.2f"
        )

        stop_loss = st.number_input(
            "Stop Loss", min_value=0.01, value=90.00, step=0.01, format="%.2f"
        )

        target_price = st.number_input(
            "Target Price", min_value=0.01, value=120.00, step=0.01, format="%.2f"
        )

        if st.button("Calculate Risk-Reward Ratio"):
            ratio, statement = calculate_risk_reward_ratio(
                entry_price, stop_loss, target_price
            )

            # Display the risk-reward ratio with styling
            st.markdown(f"### Risk-Reward Ratio: **1:{(1/ratio):.1f}**")
            st.markdown(f"*{statement}*")

            # Visualize the risk-reward
            fig = go.Figure()

            # Create visual representation of entry, stop, and target
            if entry_price > stop_loss:  # Long position
                fig.add_trace(
                    go.Scatter(
                        x=["Entry", "Stop Loss", "Target"],
                        y=[entry_price, stop_loss, target_price],
                        mode="lines+markers",
                        name="Price Levels",
                        marker=dict(size=12),
                    )
                )

                # Add risk and reward areas
                fig.add_shape(
                    type="rect",
                    x0=-0.5,
                    y0=stop_loss,
                    x1=0.5,
                    y1=entry_price,
                    fillcolor="rgba(255,0,0,0.2)",
                    line=dict(width=0),
                    name="Risk",
                )

                fig.add_shape(
                    type="rect",
                    x0=1.5,
                    y0=entry_price,
                    x1=2.5,
                    y1=target_price,
                    fillcolor="rgba(0,255,0,0.2)",
                    line=dict(width=0),
                    name="Reward",
                )
            else:  # Short position
                fig.add_trace(
                    go.Scatter(
                        x=["Entry", "Stop Loss", "Target"],
                        y=[entry_price, stop_loss, target_price],
                        mode="lines+markers",
                        name="Price Levels",
                        marker=dict(size=12),
                    )
                )

                # Add risk and reward areas
                fig.add_shape(
                    type="rect",
                    x0=-0.5,
                    y0=entry_price,
                    x1=0.5,
                    y1=stop_loss,
                    fillcolor="rgba(255,0,0,0.2)",
                    line=dict(width=0),
                    name="Risk",
                )

                fig.add_shape(
                    type="rect",
                    x0=1.5,
                    y0=target_price,
                    x1=2.5,
                    y1=entry_price,
                    fillcolor="rgba(0,255,0,0.2)",
                    line=dict(width=0),
                    name="Reward",
                )

            fig.update_layout(
                title="Risk-Reward Visualization",
                template="plotly_white",
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Position Size Calculator")

        # Input fields for position size calculator
        account_balance = st.number_input(
            "Account Balance",
            min_value=100.0,
            value=10000.0,
            step=100.0,
            format="%.2f",
        )

        risk_percentage = st.number_input(
            "Risk Percentage (%)",
            min_value=0.1,
            max_value=10.0,
            value=2.0,
            step=0.1,
            format="%.1f",
        )

        entry_price_pos = st.number_input(
            "Entry Price",
            min_value=0.01,
            value=100.00,
            step=0.01,
            key="entry_price_pos",
            format="%.2f",
        )

        stop_loss_pos = st.number_input(
            "Stop Loss",
            min_value=0.01,
            value=90.00,
            step=0.01,
            key="stop_loss_pos",
            format="%.2f",
        )

        if st.button("Calculate Position Size"):
            position_size, dollar_risk, statement = calculate_position_size(
                account_balance, risk_percentage, entry_price_pos, stop_loss_pos
            )

            # Display the position size with styling
            st.markdown(f"### Position Size: **{position_size:,} shares**")
            st.markdown(f"*{statement}*")

            # Create visual representation of the risk
            fig = go.Figure()

            # Pie chart showing risked vs protected capital
            fig.add_trace(
                go.Pie(
                    labels=["Amount at Risk", "Protected Capital"],
                    values=[dollar_risk, account_balance - dollar_risk],
                    hole=0.5,
                    marker_colors=["rgba(255,0,0,0.7)", "rgba(0,128,0,0.7)"],
                )
            )

            fig.update_layout(
                title="Account Risk Visualization", template="plotly_white"
            )

            # Add annotation in the center
            fig.add_annotation(
                text=f"{risk_percentage}%<br>Risk",
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False,
            )

            st.plotly_chart(fig, use_container_width=True)
