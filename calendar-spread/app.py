"""
Streamlit app to view NSE futures entities and run backtests.
"""

import time

import pandas as pd
import streamlit as st
from futures_data import backtest_calendar_spread, get_continuous_futures_data
from nse_api import NSEDataFetcher


def display_backtest_results(
    trades_df: pd.DataFrame, backtest_df: pd.DataFrame = None
) -> None:
    """Display backtest results in a formatted way."""
    if not trades_df.empty:
        # Trade Statistics
        col1, col2 = st.columns(2)
        with col1:
            total_pnl = trades_df["PnL"].sum()
            avg_pnl = trades_df["PnL"].mean()
            avg_holding = trades_df["Holding_Days"].mean()
            st.metric("Total P&L", f"₹{total_pnl:.2f}")
            st.metric("Avg P&L/Trade", f"₹{avg_pnl:.2f}")
            st.metric("Avg Holding Days", f"{avg_holding:.1f}")

        with col2:
            win_rate = len(trades_df[trades_df["PnL"] > 0]) / len(trades_df) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
            # Get losing trades (PnL < 0) for max loss
            losing_trades = trades_df[trades_df["PnL"] < 0]
            max_loss = losing_trades["PnL"].min() if not losing_trades.empty else 0

            # Get winning trades (PnL > 0) for min/max profits
            winning_trades = trades_df[trades_df["PnL"] > 0]
            min_profit = winning_trades["PnL"].min() if not winning_trades.empty else 0
            max_profit = winning_trades["PnL"].max() if not winning_trades.empty else 0

            st.metric("Max Loss", f"₹{max_loss:.2f}")
            st.metric("Min Profit", f"₹{min_profit:.2f}")
            st.metric("Max Profit", f"₹{max_profit:.2f}")

        # Spread Statistics
        if backtest_df is not None:
            st.divider()
            st.subheader("Spread Statistics")
            spread_col1, spread_col2 = st.columns(2)

            with spread_col1:
                spread_mean = backtest_df["Spread"].mean()
                spread_std = backtest_df["Spread"].std()
                st.metric("Mean Spread", f"₹{spread_mean:.2f}")
                st.metric("Spread Std Dev", f"₹{spread_std:.2f}")

            with spread_col2:
                spread_high = spread_mean + spread_std
                spread_low = spread_mean - spread_std
                st.metric("Highest Spread", f"₹{spread_high:.2f}")
                st.metric("Lowest Spread", f"₹{spread_low:.2f}")

    else:
        st.warning("No trades were generated during the backtest period")


def display_stocks(stocks_subset: pd.DataFrame) -> None:
    """
    Display stock information in expandable sections.

    Args:
        stocks_subset: DataFrame containing stock information to display
    """
    # Display each stock in an expander
    for idx, row in stocks_subset.iterrows():
        # Define base signal types
        signal_info = {
            "BUY": {"color": "green", "emoji": "🟢"},
            "SELL": {"color": "red", "emoji": "🔴"},
            "NEUTRAL": {"color": "gray", "emoji": "⚪"},
        }

        # Get signal style based on signal content
        signal = row["Signal"]
        if "BUY" in signal.upper():
            signal_style = signal_info["BUY"]
        elif "SELL" in signal.upper():
            signal_style = signal_info["SELL"]
        else:
            signal_style = signal_info["NEUTRAL"]

        trades_emoji = "✅" if row["Total Trades"] >= 5 else ""
        holding_emoji = "✅" if float(row["Avg Holding Period"]) < 5 else ""

        # Get spread statistics
        if row["Symbol"] in st.session_state.backtest_results:
            spread_mean = st.session_state.backtest_results[row["Symbol"]][
                "backtest_df"
            ]["Spread"].mean()
            spread_std = st.session_state.backtest_results[row["Symbol"]][
                "backtest_df"
            ]["Spread"].std()
            spread_high = spread_mean + spread_std
            spread_low = spread_mean - spread_std
        else:
            spread_high = spread_low = 0

        # Calculate wins and losses
        wins_losses = ""
        if row["Symbol"] in st.session_state.backtest_results:
            trades_df = st.session_state.backtest_results[row["Symbol"]]["trades_df"]
            if not trades_df.empty:
                wins = len(trades_df[trades_df["PnL"] > 0])
                losses = len(trades_df[trades_df["PnL"] <= 0])
                wins_losses = f"&nbsp;&nbsp;&nbsp; W/L: 🟢{wins}/🔴{losses}"

        label_content = (
            f"### {row['Symbol']} - {row['Underlying']}"
            f"&nbsp;&nbsp;&nbsp; Trades: {row['Total Trades']} {trades_emoji} "
            f"&nbsp;&nbsp;&nbsp; Holding: {row['Avg Holding Period']:.1f} days {holding_emoji} "
            f"&nbsp;&nbsp;&nbsp; High: ₹{spread_high:.1f} Low: ₹{spread_low:.1f} "
            f"{wins_losses}"
            f"&nbsp;&nbsp;&nbsp; Signal: :{signal_style['color']}[{signal}] {signal_style['emoji']} "
            f"{'&nbsp;&nbsp;&nbsp; 💵' if 'Fresh' in row['Signal'] else ''}"
        )

        with st.expander(label_content):
            if row["Symbol"] in st.session_state.backtest_results:
                results = st.session_state.backtest_results[row["Symbol"]]

                st.subheader(f"Backtest Results for {row['Symbol']}")
                display_backtest_results(results["trades_df"], results["backtest_df"])

                st.subheader("Trade Details")
                if st.button(
                    "View Trade Details(last 100 days)", key=f"trades_{row['Symbol']}"
                ):
                    st.dataframe(
                        results["trades_df"].sort_values("Entry_Date"),
                        hide_index=True,
                        use_container_width=True,
                    )

                st.subheader("Continuous Futures Data")
                if st.button("View Data Table", key=f"data_{row['Symbol']}"):
                    st.dataframe(
                        results["backtest_df"],
                        hide_index=True,
                        use_container_width=True,
                    )


def calculate_win_rate(symbol: str) -> float:
    """Calculate win rate for a given symbol from backtest results."""
    if symbol not in st.session_state.backtest_results:
        return 0.0

    trades_df = st.session_state.backtest_results[symbol]["trades_df"]
    if trades_df.empty:
        return 0.0

    wins = len(trades_df[trades_df["PnL"] > 0])
    total_trades = len(trades_df)
    return (wins / total_trades * 100) if total_trades > 0 else 0.0


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="NSE Calendar Spread Trading Strategy",
        page_icon="📈",
        layout="wide",
    )

    # Initialize NSE data fetcher and fetch initial data
    with st.spinner("Fetching data from NSE..."):
        nse = NSEDataFetcher()
        futures_entities = nse.get_underlying_info()

    # Initialize session state for storing backtest results if not exists
    if "backtest_results" not in st.session_state:
        start_time = time.time()
        st.session_state.backtest_results = {}

        # Create containers for progress and results
        progress_container = st.container()

        with progress_container:
            stocks = futures_entities["stocks"]
            # stocks = stocks[:30]
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_text = st.empty()

        for i, stock in enumerate(stocks):
            symbol = stock["symbol"]
            with progress_container:
                status_text.text(f"Processing {symbol} ({i+1}/{len(stocks)})")
                elapsed_time = time.time() - start_time
                time_text.text(f"Time elapsed: {elapsed_time:.1f} seconds")

            # Fetch and backtest
            continuous_df = get_continuous_futures_data(
                symbol, use_cache_for_future=False
            )
            if continuous_df.empty:
                continue

            backtest_df, trades_df = backtest_calendar_spread(continuous_df)
            if trades_df.empty:
                continue

            # Calculate signal thresholds
            spread_mean = backtest_df["Spread"].mean()
            spread_std = backtest_df["Spread"].std()
            upper_threshold = spread_mean + spread_std
            lower_threshold = spread_mean - spread_std

            # Get current data
            current_spread = backtest_df["Spread"].iloc[-1]
            current_date = backtest_df["Date"].iloc[-1]

            # Default signal
            signal = "NEUTRAL"

            # Get last trade info
            last_trade = trades_df.sort_values("Exit_Date").iloc[-1]
            last_exit_date = pd.to_datetime(last_trade["Exit_Date"])

            # Filter data after last trade exit
            post_trade_data = backtest_df[backtest_df["Date"] > last_exit_date]

            if post_trade_data.empty:
                # New signals on first day after trade
                if current_spread > upper_threshold:
                    signal = "SELL (Fresh)"
                elif current_spread < lower_threshold:
                    signal = "BUY (Fresh)"
            else:
                signal_start_date = None
                signal_type = None

                # Check for SELL signal
                if current_spread > upper_threshold:
                    sell_signals = post_trade_data[
                        post_trade_data["Spread"] > upper_threshold
                    ]
                    if not sell_signals.empty:
                        signal_start_date = sell_signals.iloc[0]["Date"]
                        signal_type = "SELL"

                # Check for BUY signal
                elif current_spread < lower_threshold:
                    buy_signals = post_trade_data[
                        post_trade_data["Spread"] < lower_threshold
                    ]
                    if not buy_signals.empty:
                        signal_start_date = buy_signals.iloc[0]["Date"]
                        signal_type = "BUY"

                if signal_start_date is not None:
                    days_active = (current_date - signal_start_date).days
                    signal = f"{signal_type} ({'Fresh' if days_active <= 1 else f'Active {days_active}d'})"

            print(f"signal for {symbol}: {signal}")
            st.session_state.backtest_results[symbol] = {
                "total_trades": len(trades_df),
                "avg_holding": trades_df["Holding_Days"].mean(),
                "signal": signal,
                "trades_df": trades_df,
                "backtest_df": continuous_df,
                "underlying": stock["underlying"],
            }

            # Update progress
            progress = (i + 1) / len(stocks)
            progress_bar.progress(progress)

        # Display final time taken
        final_time = time.time() - start_time
        with progress_container:
            st.success(
                f"Completed processing {len(stocks)} stocks in {final_time:.1f} seconds"
            )

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        time_text.empty()

    st.header("Stock Futures")
    st.write(f"Total stocks: {len(futures_entities['stocks'])}")

    # Create DataFrame directly without search filter
    stocks_df = pd.DataFrame(
        [
            {"Symbol": stock["symbol"], "Underlying": stock["underlying"]}
            for stock in futures_entities["stocks"]
        ]
    )

    # Initialize columns with values from session state or defaults
    stocks_df["Total Trades"] = stocks_df["Symbol"].apply(
        lambda x: st.session_state.backtest_results.get(x, {}).get("total_trades", 0)
    )
    stocks_df["Avg Holding Period"] = stocks_df["Symbol"].apply(
        lambda x: st.session_state.backtest_results.get(x, {}).get("avg_holding", 0)
    )
    stocks_df["Signal"] = stocks_df["Symbol"].apply(
        lambda x: st.session_state.backtest_results.get(x, {}).get("signal", "N/A")
    )
    # Add win rate column
    stocks_df["Win Rate"] = stocks_df["Symbol"].apply(calculate_win_rate)

    # Sort stocks by signal order and win rate within each signal type
    def get_signal_order(signal):
        if "fresh" in signal.lower():
            if "sell" in signal.lower():
                return 0  # Fresh SELL signals first
            else:
                return 1  # Fresh BUY signals second
        elif "active" in signal.lower():
            if "sell" in signal.lower():
                return 2  # Active SELL signals second
            else:
                return 3  # Active BUY signals third
        else:
            return 4  # NEUTRAL signals last

    # Sort stocks by signal order first, then by win rate within each signal group
    stocks_df["signal_order"] = stocks_df["Signal"].apply(get_signal_order)
    stocks_df = stocks_df.sort_values(
        ["signal_order", "Total Trades", "Win Rate"], ascending=[True, False, False]
    )

    # Filter out stocks that signal NEUTRAL
    neutral_stocks_df = stocks_df[
        (stocks_df["Signal"] == "NEUTRAL") | (stocks_df["Signal"] == "N/A")
    ]
    non_neutral_stocks_df = stocks_df[
        (stocks_df["Signal"] != "NEUTRAL") & (stocks_df["Signal"] != "N/A")
    ]

    # Split stocks into fresh and active (they'll already be sorted by win rate)
    fresh_stocks = non_neutral_stocks_df[
        non_neutral_stocks_df["Signal"].str.contains("Fresh", case=False)
    ]
    active_stocks = non_neutral_stocks_df[
        ~non_neutral_stocks_df["Signal"].str.contains("Fresh", case=False)
    ]

    # Create tabs for fresh, active, and neutral stocks
    fresh_tab, active_tab, neutral_tab = st.tabs(
        [
            f"Fresh Signals ({len(fresh_stocks)})",
            f"Active Signals ({len(active_stocks)})",
            f"Other Stocks ({len(neutral_stocks_df)})",
        ]
    )

    # Display stocks in respective tabs
    with fresh_tab:
        if len(fresh_stocks) == 0:
            st.info("No fresh signals available")
        else:
            display_stocks(fresh_stocks)

    with active_tab:
        if len(active_stocks) == 0:
            st.info("No active signals available")
        else:
            display_stocks(active_stocks)

    with neutral_tab:
        if len(neutral_stocks_df) == 0:
            st.info("No other stocks available")
        else:
            display_stocks(neutral_stocks_df)

    # Add footer with refresh button
    st.divider()
    if st.button("🔄 Refresh Data"):
        st.session_state.backtest_results = {}  # Clear backtest results
        st.rerun()

    st.markdown(
        """
        <div style='text-align: center; color: grey; padding: 10px;'>
        Data sourced from NSE India • Refreshed on demand
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
