import numpy as np
import pandas as pd
import yfinance as yf


def detect_patterns(symbol, period="1mo", interval="1d"):
    """
    Detect various candlestick patterns for a given stock

    Args:
        symbol (str): Stock ticker symbol
        period (str): Time period to analyze (default: '1mo')
        interval (str): Data interval (default: '1d')

    Returns:
        dict: Dictionary containing detected patterns
    """
    # Download stock data
    stock = yf.Ticker(symbol)
    df = stock.history(period=period, interval=interval)

    # Calculate candle body and shadows
    df["Body"] = df["Close"] - df["Open"]
    df["Upper_Shadow"] = df["High"] - df[["Open", "Close"]].max(axis=1)
    df["Lower_Shadow"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
    df["Body_Size"] = abs(df["Body"])

    # Calculate average body size for relative comparisons
    avg_body = df["Body_Size"].mean()

    patterns = {}

    # Marubozu detection (small shadows allowed)
    shadow_threshold = 0.15  # Increased from 0.1 to allow slightly larger shadows
    marubozu_bullish = (
        (df["Body"] > 0)
        & (df["Upper_Shadow"] < df["Body_Size"] * shadow_threshold)
        & (df["Lower_Shadow"] < df["Body_Size"] * shadow_threshold)
        & (df["Body_Size"] > avg_body * 0.8)
    )  # Should be a relatively large candle

    marubozu_bearish = (
        (df["Body"] < 0)
        & (df["Upper_Shadow"] < df["Body_Size"] * shadow_threshold)
        & (df["Lower_Shadow"] < df["Body_Size"] * shadow_threshold)
        & (df["Body_Size"] > avg_body * 0.8)
    )  # Should be a relatively large candle

    # Doji and Spinning Top detection
    body_threshold = 0.15  # Increased from 0.1 for more flexible Doji detection
    doji = (df["Body_Size"] < avg_body * body_threshold) & (
        (df["Upper_Shadow"] > df["Body_Size"]) | (df["Lower_Shadow"] > df["Body_Size"])
    )

    # Increased from 0.3
    spinning_top = (
        (df["Body_Size"] < avg_body * 0.4)
        & (df["Upper_Shadow"] > df["Body_Size"] * 0.8)
        & (df["Lower_Shadow"] > df["Body_Size"] * 0.8)
    )

    # Hammer, Hanging Man, and Shooting Star detection
    body_pos_threshold = 0.4  # Increased from 0.3
    shadow_length_threshold = 1.8  # Decreased from 2.0 for more flexibility

    hammer = (
        (df["Lower_Shadow"] > df["Body_Size"] * shadow_length_threshold)
        & (df["Upper_Shadow"] < df["Body_Size"] * body_pos_threshold)
        & (df["Body"] > 0)
    )

    hanging_man = (
        (df["Lower_Shadow"] > df["Body_Size"] * shadow_length_threshold)
        & (df["Upper_Shadow"] < df["Body_Size"] * body_pos_threshold)
        & (df["Body"] < 0)
    )

    shooting_star = (df["Upper_Shadow"] > df["Body_Size"] * shadow_length_threshold) & (
        df["Lower_Shadow"] < df["Body_Size"] * body_pos_threshold
    )

    # Multi-candlestick pattern detection
    # Engulfing patterns
    bullish_engulfing = (
        (df["Body"].shift(1) < 0)
        & (df["Body"] > 0)
        & (df["Open"] < df["Close"].shift(1))
        & (df["Close"] > df["Open"].shift(1))
        & (df["Body_Size"] > df["Body_Size"].shift(1) * 0.95)
    )  # 95% to be more flexible

    bearish_engulfing = (
        (df["Body"].shift(1) > 0)
        & (df["Body"] < 0)
        & (df["Close"] < df["Open"].shift(1))
        & (df["Open"] > df["Close"].shift(1))
        & (df["Body_Size"] > df["Body_Size"].shift(1) * 0.95)
    )

    # Piercing and Dark Cloud patterns
    piercing = (
        (df["Body"].shift(1) < 0)
        & (df["Body"] > 0)
        & (df["Open"] < df["Low"].shift(1))
        & (df["Close"] > (df["Open"].shift(1) + df["Close"].shift(1)) / 2)
        & (df["Close"] < df["Open"].shift(1))
    )

    dark_cloud = (
        (df["Body"].shift(1) > 0)
        & (df["Body"] < 0)
        & (df["Open"] > df["High"].shift(1))
        & (df["Close"] < (df["Open"].shift(1) + df["Close"].shift(1)) / 2)
        & (df["Close"] > df["Close"].shift(1))
    )

    # Harami patterns
    harami_bullish = (
        (df["Body"].shift(1) < 0)
        & (df["Body"] > 0)
        & (df["High"] < df["Open"].shift(1))
        & (df["Low"] > df["Close"].shift(1))
        & (df["Body_Size"] < abs(df["Body"].shift(1)) * 0.6)
    )  # More flexible size requirement

    harami_bearish = (
        (df["Body"].shift(1) > 0)
        & (df["Body"] < 0)
        & (df["High"] < df["Close"].shift(1))
        & (df["Low"] > df["Open"].shift(1))
        & (df["Body_Size"] < df["Body_Size"].shift(1) * 0.6)
    )

    # Morning Star and Evening Star patterns
    morning_star = (
        (df["Body"].shift(2) < 0)
        & (abs(df["Body"].shift(1)) < avg_body * 0.3)
        & (df["Body"] > 0)
        & (df["Close"] > (df["Open"].shift(2) + df["Close"].shift(2)) / 2)
    )

    evening_star = (
        (df["Body"].shift(2) > 0)
        & (abs(df["Body"].shift(1)) < avg_body * 0.3)
        & (df["Body"] < 0)
        & (df["Close"] < (df["Open"].shift(2) + df["Close"].shift(2)) / 2)
    )

    # Store results
    patterns = {
        "Bullish Marubozu": df.index[marubozu_bullish].tolist(),
        "Bearish Marubozu": df.index[marubozu_bearish].tolist(),
        "Doji": df.index[doji].tolist(),
        "Spinning Top": df.index[spinning_top].tolist(),
        "Hammer": df.index[hammer].tolist(),
        "Hanging Man": df.index[hanging_man].tolist(),
        "Shooting Star": df.index[shooting_star].tolist(),
        "Bullish Engulfing": df.index[bullish_engulfing].tolist(),
        "Bearish Engulfing": df.index[bearish_engulfing].tolist(),
        "Piercing Line": df.index[piercing].tolist(),
        "Dark Cloud Cover": df.index[dark_cloud].tolist(),
        "Bullish Harami": df.index[harami_bullish].tolist(),
        "Bearish Harami": df.index[harami_bearish].tolist(),
        "Morning Star": df.index[morning_star].tolist(),
        "Evening Star": df.index[evening_star].tolist(),
    }

    return patterns


def print_patterns(patterns):
    """Print detected patterns in a readable format"""
    print("\nDetected Candlestick Patterns:")
    print("-" * 30)
    for pattern, dates in patterns.items():
        if dates:
            print(f"\n{pattern}:")
            for date in dates:
                print(f"  - {date.strftime('%Y-%m-%d')}")


def get_recent_patterns(symbol, lookback_days=5, period="3mo", interval="1d"):
    """
    Get patterns for the most recent trading days

    Args:
        symbol (str): Stock ticker symbol
        lookback_days (int): Number of recent days to check
        period (str): Time period to analyze (default: '3mo')
        interval (str): Data interval (default: '1d')

    Returns:
        dict: Dictionary containing recent patterns
    """
    patterns = detect_patterns(symbol, period=period, interval=interval)

    # Get current date
    current_date = pd.Timestamp.now().date()

    # Filter patterns for recent dates
    recent_patterns = {}
    for pattern, dates in patterns.items():
        recent_dates = [
            date for date in dates if (current_date - date.date()).days <= lookback_days
        ]
        if recent_dates:
            recent_patterns[pattern] = recent_dates

    return recent_patterns


def print_recent_patterns(patterns):
    """Print recent patterns in a readable format"""
    if not patterns:
        print("\nNo patterns detected in recent days.")
        return

    print("\nRecent Candlestick Patterns:")
    print("-" * 30)
    for pattern, dates in patterns.items():
        if dates:
            print(f"\n{pattern}:")
            for date in sorted(dates, reverse=True):
                print(f"  - {date.strftime('%Y-%m-%d')}")


# Example usage
if __name__ == "__main__":
    symbol = "INFY.NS"  # Example: Infosys
    recent_patterns = get_recent_patterns(symbol)
    print_recent_patterns(recent_patterns)
