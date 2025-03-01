import json
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from candle_stick_patterns import get_recent_patterns, print_recent_patterns


def get_stock_history(ticker_symbol, start_date, end_date):
    """
    Get stock history data with file-based caching to avoid repeated downloads.

    Args:
        ticker_symbol (str): Stock ticker symbol
        start_date (datetime): Start date for history
        end_date (datetime): End date for history

    Returns:
        pandas.DataFrame: Historical data
    """
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(start=start_date, end=end_date)

    return hist


def check_volume_surge(ticker_symbol):
    """
    Check if stock's current day volume is higher than the last 10 working days.

    Args:
        ticker_symbol (str): Stock ticker symbol (e.g., 'AAPL' for Apple)

    Returns:
        tuple: (bool, float) - (whether volume surged, % increase from average)
    """
    try:
        # Get stock data for last 15 days (to ensure we have 10 working days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=15)

        # Fetch historical data using cache
        hist = get_stock_history(ticker_symbol, start_date, end_date)

        if hist.empty:
            return False, 0, 0, 0, 0

        # pdb.set_trace()

        # Get the latest volume
        current_volume = hist["Volume"].iloc[-1]

        # Get the previous 10 working days volumes
        previous_volumes = hist["Volume"].iloc[-11:-1]

        avg_volume = previous_volumes.mean()

        # Calculate percentage increase
        percent_increase = ((current_volume - avg_volume) / avg_volume) * 100

        # Check if current volume is higher than all previous 10 days
        is_surge = current_volume > avg_volume

        return is_surge, current_volume, avg_volume, previous_volumes, percent_increase

    except Exception as e:
        print(f"Error checking volume for {ticker_symbol}: {str(e)}")
        return False, 0, 0, 0, 0


def get_stocks(file_name):
    """
    Get a list of stock symbols from a CSV file.

    Args:
        file_name (str): Path to the CSV file containing stock symbols

    Returns:
        list: List of stock symbols
    """
    directory = "data"
    file_name = f"{directory}/{file_name}"
    df = pd.read_csv(file_name)
    return df["Symbol"].tolist()


def get_stocks_from_json(index_name):
    """
    Get a list of stock symbols from the nifty_indices.json file.

    Args:
        index_name (str): Name of the index to get stocks for

    Returns:
        list: List of stock symbols
    """
    try:
        with open("data/nifty_indices.json", "r") as f:
            indices_data = json.load(f)

        if index_name.lower() in indices_data:
            return indices_data[index_name.lower()]
        else:
            print(f"Index {index_name} not found in nifty_indices.json")
            return []
    except Exception as e:
        print(f"Error loading nifty_indices.json: {str(e)}")
        return []


def main():
    # Load available indices
    try:
        with open("data/nifty_indices.json", "r") as f:
            indices_data = json.load(f)

        # Use nifty100 by default
        index_name = "nifty100"
        tickers = indices_data.get(index_name, [])
    except Exception as e:
        print(f"Error loading indices: {str(e)}")
        # Fallback to nifty100 CSV if JSON fails
        tickers = get_stocks("ind_nifty100list.csv")

    surge_results = []

    for ticker in tickers:
        ticker_ns = ticker + ".NS"
        is_surge, current_volume, avg_volume, previous_volumes, percent_increase = (
            check_volume_surge(ticker_ns)
        )

        if is_surge and percent_increase > 49:
            surge_results.append(
                {
                    "ticker": ticker_ns,
                    "percent_increase": percent_increase,
                    "current_volume": current_volume,
                    "avg_volume": avg_volume,
                }
            )

    # Sort results by percent_increase in descending order
    surge_results.sort(key=lambda x: x["percent_increase"], reverse=True)

    # Print sorted results
    if surge_results:
        print("\nToday's Stocks:")
        print("-" * 80)
        for result in surge_results:
            print(
                f"{result['ticker']}: Volume surge detected! {result['percent_increase']:.2f}% above 10-day average. "
                f"Current Volume: {result['current_volume']}, Average Volume: {int(result['avg_volume'])}"
            )

            recent_patterns = get_recent_patterns(result["ticker"])
            print_recent_patterns(recent_patterns)
            print("\n" + "-" * 80 + "\n")
    else:
        print("No volume surges detected.")


if __name__ == "__main__":
    main()
