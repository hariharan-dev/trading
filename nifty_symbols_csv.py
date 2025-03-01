"""
Script to download Nifty 50, 100, and 200 stock symbols from NSE India website.
This approach downloads the data directly from the NSE India website.
"""

import io
import json
import os
import random
import time

import pandas as pd
import requests

# Create data directory if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

# URLs for the Nifty indices CSV files
NIFTY_CSV_URLS = {
    "nifty50": ("https://archives.nseindia.com/content/indices/ind_nifty50list.csv"),
    "nifty100": ("https://archives.nseindia.com/content/indices/ind_nifty100list.csv"),
    "nifty200": ("https://archives.nseindia.com/content/indices/ind_nifty200list.csv"),
    "nifty500": ("https://archives.nseindia.com/content/indices/ind_nifty500list.csv"),
    "nifty_next_50": (
        "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv"
    ),
    "nifty_midcap_50": (
        "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv"
    ),
    "nifty_smallcap_50": (
        "https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv"
    ),
    "nifty_it": ("https://archives.nseindia.com/content/indices/ind_niftyitlist.csv"),
    "nifty_bank": (
        "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv"
    ),
}


def download_nifty_csv():
    """
    Download Nifty 50, 100, and 200 CSV files from NSE India archives

    Returns:
        dict: Dictionary containing Nifty 50, 100, and 200 symbols
    """
    print("Downloading Nifty indices CSV files from NSE India archives...")

    # Headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/99.0.4844.84 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    result = {"nifty50": [], "nifty100": [], "nifty200": []}

    # Download each CSV file
    for index_name, url in NIFTY_CSV_URLS.items():
        try:
            print(f"Downloading {index_name} CSV from {url}...")

            # Download the CSV
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                # Parse CSV content
                csv_content = response.content.decode("utf-8")
                df = pd.read_csv(io.StringIO(csv_content))

                # Extract symbols without adding .NS suffix
                if "Symbol" in df.columns:
                    symbols = df["Symbol"].tolist()
                    result[index_name] = symbols
                    print(f"Found {len(symbols)} symbols for {index_name}")
                else:
                    print(f"No Symbol column found in {index_name} CSV")
                    # Try alternative column names
                    possible_columns = [
                        "Symbol",
                        "SYMBOL",
                        "symbol",
                        "Ticker",
                        "TICKER",
                    ]
                    for col in possible_columns:
                        if col in df.columns:
                            symbols = df[col].tolist()
                            result[index_name] = symbols
                            print(
                                f"Found {len(symbols)} symbols for {index_name} in column {col}"
                            )
                            break
            else:
                print(f"Failed to download {index_name} CSV: {response.status_code}")

        except Exception as e:
            print(f"Error downloading {index_name} CSV: {e}")

        # Add a delay to avoid hitting rate limits
        time.sleep(random.uniform(1, 2))

    return result


def save_symbols_to_json(symbols_data):
    """Save the symbols data to a JSON file"""
    if not symbols_data:
        print("No data to save")
        return

    filename = "data/nifty_indices.json"
    with open(filename, "w") as f:
        json.dump(symbols_data, f, indent=4)

    print(f"\nSaved symbols to {filename}")

    # Print summary
    for index, symbols in symbols_data.items():
        if symbols:
            print(f"  {index}: {len(symbols)} symbols")
            # Print first 5 symbols as example
            print(f"  First 5 symbols: {', '.join(symbols[:5])}")


def main():
    print("Fetching Nifty 50, 100, and 200 stock symbols from NSE India website")

    # Try downloading CSV files directly from archives
    symbols = download_nifty_csv()

    # Save to JSON file
    if symbols and any(len(symbols[index]) > 0 for index in symbols):
        save_symbols_to_json(symbols)
        print("\nSuccess! The symbols have been saved without any suffix.")
    else:
        print("\nFailed to fetch symbols from NSE India.")
        print("You may need to try again later or use a different approach.")


if __name__ == "__main__":
    main()
