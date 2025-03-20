import calendar
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from calendar_spread.nse_api import NSEDataFetcher


def get_last_thursday(year: int, month: int) -> datetime:
    """Get the last Thursday of the given month and year."""
    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day)

    while last_date.weekday() != 3:
        last_date -= timedelta(days=1)

    return last_date


def get_expiry_dates() -> List[str]:
    """Get current, near and far month expiry dates."""
    current_date = datetime.now()
    expiry_dates = []

    # Get current month expiry
    current_month_expiry = get_last_thursday(current_date.year, current_date.month)

    # If current date is past current month expiry, move to next month
    if current_date > current_month_expiry:
        current_date = current_date.replace(day=1) + timedelta(days=32)
        current_month_expiry = get_last_thursday(current_date.year, current_date.month)

    # Get next three months' expiry dates
    for _ in range(3):
        expiry_dates.append(current_month_expiry.strftime("%d-%b-%Y"))
        next_month = current_month_expiry.replace(day=1) + timedelta(days=32)
        current_month_expiry = get_last_thursday(next_month.year, next_month.month)
    return expiry_dates


def get_continuous_futures_data(
    symbol: str, use_cache_for_future: bool = False
) -> pd.DataFrame:
    """
    Create a continuous futures table with current and near month data
    for last 200 days from current date.

    Args:
        symbol: Stock symbol (e.g., 'SBIN')
    """
    try:
        # Initialize NSE data fetcher
        nse = NSEDataFetcher()

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=200)

        # Extend end_date by 1 month for fetching near month data
        extended_end_date = end_date + timedelta(days=31)
        end_date_str = extended_end_date.strftime("%d-%m-%Y")
        start_date_str = start_date.strftime("%d-%m-%Y")

        # Get all expiry dates needed (last 8 months to cover 200 days)
        expiry_dates = []
        current_date = start_date

        # Get first month expiry
        current_expiry = get_last_thursday(current_date.year, current_date.month).date()

        # Get 9 months of expiry dates to ensure coverage including the extended month
        for _ in range(9):
            expiry_date = current_expiry.strftime("%d-%b-%Y")
            if current_expiry > start_date:  # Only add if expiry is after start date
                expiry_dates.append(expiry_date)
            next_month = current_expiry.replace(day=1) + timedelta(days=32)
            current_expiry = get_last_thursday(next_month.year, next_month.month).date()

        # Format dates for API
        print(f"Date Range: {start_date_str} to {end_date_str}")
        print("Expiry dates to fetch:", expiry_dates)

        # Fetch data for each expiry
        futures_data = {}
        all_trading_dates = set()  # Keep track of actual trading dates
        for expiry in expiry_dates:
            print(f"\nFetching data for expiry: {expiry}")
            df = nse.get_futures_data(
                symbol, start_date_str, end_date_str, expiry, use_cache_for_future
            )
            if df is not None and not df.empty:
                futures_data[expiry] = df
                # Collect actual trading dates
                all_trading_dates.update(df["Date"].dt.date)

        # Sort trading dates for ordered processing
        all_trading_dates = sorted(list(all_trading_dates))

        # Create continuous futures table using only actual trading dates
        result_data = []
        for date in all_trading_dates:
            row = {"Date": date}

            # Find current month contract
            current_expiry = None
            for expiry in expiry_dates:
                expiry_date = datetime.strptime(expiry, "%d-%b-%Y").date()
                if date <= expiry_date:
                    current_expiry = expiry
                    break

            # Find near month contract
            near_expiry = None
            if current_expiry:
                current_expiry_date = datetime.strptime(
                    current_expiry, "%d-%b-%Y"
                ).date()
                for expiry in expiry_dates:
                    expiry_date = datetime.strptime(expiry, "%d-%b-%Y").date()
                    if expiry_date > current_expiry_date:
                        near_expiry = expiry
                        break

            # Get closing prices (only for actual trading dates)
            if current_expiry and current_expiry in futures_data:
                current_data = futures_data[current_expiry]
                matching_rows = current_data[current_data["Date"].dt.date == date]
                if not matching_rows.empty:
                    row["Current Month"] = matching_rows["Close"].iloc[0]
                else:
                    row["Current Month"] = None

            if near_expiry and near_expiry in futures_data:
                near_data = futures_data[near_expiry]
                matching_rows = near_data[near_data["Date"].dt.date == date]
                if not matching_rows.empty:
                    row["Near Month"] = matching_rows["Close"].iloc[0]
                else:
                    row["Near Month"] = None

            result_data.append(row)

        # Create DataFrame and handle missing values
        result_df = pd.DataFrame(result_data)

        # Add expiry information
        result_df["Current Month Expiry"] = None
        result_df["Near Month Expiry"] = None

        # Assign expiry information (only for actual trading dates)
        for idx, row in result_df.iterrows():
            date = row["Date"]
            for expiry in expiry_dates:
                expiry_date = datetime.strptime(expiry, "%d-%b-%Y").date()
                if date <= expiry_date:
                    result_df.loc[idx, "Current Month Expiry"] = expiry
                    # Find next expiry for near month
                    next_expiry = None
                    for next_exp in expiry_dates:
                        next_exp_date = datetime.strptime(next_exp, "%d-%b-%Y").date()
                        if next_exp_date > expiry_date:
                            next_expiry = next_exp
                            break
                    result_df.loc[idx, "Near Month Expiry"] = next_expiry
                    break

        # Fill missing values only within each expiry period and only for actual trading dates
        for expiry in expiry_dates:
            # Fill Current Month prices
            mask = result_df["Current Month Expiry"] == expiry
            if mask.any():
                expiry_data = result_df.loc[mask].copy()
                expiry_data["Current Month"] = expiry_data["Current Month"].ffill()
                result_df.loc[mask, "Current Month"] = expiry_data["Current Month"]

            # Fill Near Month prices
            mask = result_df["Near Month Expiry"] == expiry
            if mask.any():
                expiry_data = result_df.loc[mask].copy()
                expiry_data["Near Month"] = expiry_data["Near Month"].ffill()
                result_df.loc[mask, "Near Month"] = expiry_data["Near Month"]

        # Calculate spread (Near Month - Current Month)
        result_df["Spread"] = result_df["Near Month"] - result_df["Current Month"]

        # Remove rows where both current and near month are None
        result_df = result_df.dropna(subset=["Current Month", "Near Month"], how="all")

        # Reorder columns to put Spread after Near Month
        column_order = [
            "Date",
            "Current Month",
            "Near Month",
            "Spread",
            "Current Month Expiry",
            "Near Month Expiry",
        ]
        result_df = result_df[column_order]

        return result_df

    except Exception as e:
        print(f"Error creating continuous futures data: {str(e)}")
        return pd.DataFrame()


def backtest_calendar_spread(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backtest calendar spread strategy on the continuous futures data.
    Uses entire history for mean/std calculation, but backtests only on last 100 days.
    """
    # Ensure Date column is datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # Calculate mean and standard deviation from entire dataset
    mean_spread = df["Spread"].mean()
    std_spread = df["Spread"].std()

    # Define upper and lower bounds
    upper_bound = mean_spread + std_spread
    lower_bound = mean_spread - std_spread

    # Get testing period (last 100 days)
    testing_df = df.iloc[-150:]

    print(f"Training Period: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
    print(
        f"Testing Period: {testing_df['Date'].iloc[0]} to {testing_df['Date'].iloc[-1]}"
    )
    print(f"Mean Spread: {mean_spread:.2f}")
    print(f"Std Spread: {std_spread:.2f}")
    print(f"Upper Bound: {upper_bound:.2f}")
    print(f"Lower Bound: {lower_bound:.2f}")

    # Initialize columns for trade signals
    df["Signal"] = 0  # 1 for buy spread, -1 for sell spread
    df["Trade_Entry"] = False
    df["Trade_Exit"] = False
    df["Trade_Type"] = ""
    df["Entry_Spread"] = 0.0
    df["Exit_Spread"] = 0.0
    df["Trade_PnL"] = 0.0

    # Generate trading signals - only on testing data
    in_trade = False
    trade_type = None
    entry_spread = 0.0
    entry_date = None
    trades = []
    stop_loss_pct = 0.75  # 50% of standard deviation

    # Only iterate over the testing period
    for i in range(len(testing_df)):
        current_spread = testing_df["Spread"].iloc[i]
        current_date = testing_df["Date"].iloc[i]
        idx = testing_df.index[i]  # Get the original index for updating df

        if not in_trade:
            # Look for new trade opportunities
            if current_spread > upper_bound:
                # Sell spread signal
                in_trade = True
                trade_type = "Sell"
                entry_spread = current_spread
                entry_date = current_date
                df.loc[idx, "Signal"] = -1
                df.loc[idx, "Trade_Entry"] = True
                df.loc[idx, "Trade_Type"] = "Sell"
                df.loc[idx, "Entry_Spread"] = entry_spread

            elif current_spread < lower_bound:
                # Buy spread signal
                in_trade = True
                trade_type = "Buy"
                entry_spread = current_spread
                entry_date = current_date
                df.loc[idx, "Signal"] = 1
                df.loc[idx, "Trade_Entry"] = True
                df.loc[idx, "Trade_Type"] = "Buy"
                df.loc[idx, "Entry_Spread"] = entry_spread

        else:
            # Check for exit conditions - now including stop loss and mean reversion
            stop_loss = std_spread * stop_loss_pct

            if trade_type == "Sell":
                unrealized_pnl = entry_spread - current_spread
                # Exit if spread reverts to mean OR if loss exceeds stop loss
                if current_spread <= mean_spread or unrealized_pnl < -stop_loss:
                    exit_spread = current_spread
                    pnl = entry_spread - exit_spread  # Positive if spread decreased

            else:  # Buy trade
                unrealized_pnl = current_spread - entry_spread
                # Exit if spread reverts to mean OR if loss exceeds stop loss
                if current_spread >= mean_spread or unrealized_pnl < -stop_loss:
                    exit_spread = current_spread
                    pnl = exit_spread - entry_spread  # Positive if spread increased

            if (
                trade_type == "Sell"
                and (current_spread <= mean_spread or unrealized_pnl < -stop_loss)
            ) or (
                trade_type == "Buy"
                and (current_spread >= mean_spread or unrealized_pnl < -stop_loss)
            ):
                # Exit trade
                df.loc[idx, "Trade_Exit"] = True
                df.loc[idx, "Exit_Spread"] = exit_spread
                df.loc[idx, "Trade_PnL"] = pnl

                trades.append(
                    {
                        "Entry_Date": pd.to_datetime(entry_date),
                        "Exit_Date": pd.to_datetime(current_date),
                        "Trade_Type": trade_type,
                        "Entry_Spread": entry_spread,
                        "Exit_Spread": exit_spread,
                        "PnL": pnl,
                        "Result": "Win" if pnl > 0 else "Loss",  # Add Result column
                    }
                )

                in_trade = False
                trade_type = None
                entry_spread = 0.0
                entry_date = None

    # Create trades summary DataFrame
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df["Entry_Date"] = pd.to_datetime(trades_df["Entry_Date"])
        trades_df["Exit_Date"] = pd.to_datetime(trades_df["Exit_Date"])
        trades_df["Holding_Days"] = (
            trades_df["Exit_Date"] - trades_df["Entry_Date"]
        ).dt.days

    return df, trades_df


def main(symbol: str):
    # Set pandas to display all rows and float precision
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.float_format", lambda x: "%.2f" % x)

    # Example usage for SBI
    print(f"\nFetching continuous futures data for {symbol}...")
    continuous_df = get_continuous_futures_data(symbol)

    if not continuous_df.empty:
        print("\nContinuous Futures Data Statistics:")

        # Calculate spread
        if (
            "Current Month" in continuous_df.columns
            and "Near Month" in continuous_df.columns
        ):
            continuous_df["Spread"] = (
                continuous_df["Near Month"] - continuous_df["Current Month"]
            )
            print(continuous_df)

            # Run backtesting after showing spread statistics
            print("\n" + "=" * 50)
            print("Running Calendar Spread Backtest...")
            print("=" * 50)

            backtest_df, trades_df = backtest_calendar_spread(continuous_df)

            print("\nBacktest Results:")
            print("\nTrade Statistics:")
            if not trades_df.empty:
                print(f"Total Trades: {len(trades_df)}")
                print(f"Profitable Trades: {len(trades_df[trades_df['PnL'] > 0])}")
                print(f"Loss Making Trades: {len(trades_df[trades_df['PnL'] <= 0])}")

                total_pnl = trades_df["PnL"].sum()
                print(f"\nTotal P&L: {total_pnl:.2f}")
                print(f"Average P&L per trade: {trades_df['PnL'].mean():.2f}")
                print(
                    f"Average holding period: {trades_df['Holding_Days'].mean():.1f} days"
                )
                print(f"Max Profit: {trades_df['PnL'].max():.2f}")
                print(f"Max Loss: {trades_df['PnL'].min():.2f}")

                # Calculate win rate and risk metrics
                win_rate = len(trades_df[trades_df["PnL"] > 0]) / len(trades_df) * 100
                profit_factor = (
                    abs(
                        trades_df[trades_df["PnL"] > 0]["PnL"].sum()
                        / trades_df[trades_df["PnL"] < 0]["PnL"].sum()
                    )
                    if len(trades_df[trades_df["PnL"] < 0]) > 0
                    else float("inf")
                )

                print(f"\nWin Rate: {win_rate:.1f}%")
                print(f"Profit Factor: {profit_factor:.2f}")

                print("\nTrade Details (sorted by date):")
                print(trades_df.sort_values("Entry_Date"))
            else:
                print("No trades were generated during the backtest period")
    else:
        print("No data available")


if __name__ == "__main__":
    main("ABB")
