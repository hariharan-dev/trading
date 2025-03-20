"""
Common module for NSE India API fetching logic.
"""

import json
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class NSESession:
    _instance = None
    _session = None
    _cookies = None
    _last_cookie_refresh = None
    COOKIE_MAX_AGE = 600  # 10 minutes in seconds

    BASE_URL = "https://www.nseindia.com"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NSESession, cls).__new__(cls)
            cls._instance._init_session()
        return cls._instance

    def _init_session(self) -> None:
        """Initialize a session with retry strategy."""
        self._session = requests.Session()
        retry = Retry(
            total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._refresh_cookies()

    def _refresh_cookies(self) -> None:
        """Get fresh cookies by visiting NSE website."""
        try:
            # Visit homepage first
            self._session.get(f"{self.BASE_URL}/", headers=self.headers, timeout=30)
            time.sleep(2)  # Wait for cookies to be set

            # Visit market data page to get required cookies
            self._session.get(
                f"{self.BASE_URL}/get-quotes/derivatives?symbol=SBIN",
                headers=self.headers,
                timeout=30,
            )
            self._cookies = self._session.cookies.get_dict()
            self._last_cookie_refresh = time.time()
            print("Successfully refreshed cookies")
        except Exception as e:
            print(f"Error getting cookies: {str(e)}")
            raise

    def _should_refresh_cookies(self) -> bool:
        """Check if cookies need to be refreshed."""
        if self._last_cookie_refresh is None:
            return True
        return (time.time() - self._last_cookie_refresh) > self.COOKIE_MAX_AGE

    @property
    def session(self) -> requests.Session:
        if self._should_refresh_cookies():
            print("Cookies are older than 10 minutes, refreshing...")
            self._refresh_cookies()
        return self._session

    @property
    def cookies(self) -> dict:
        if self._should_refresh_cookies():
            print("Cookies are older than 10 minutes, refreshing...")
            self._refresh_cookies()
        return self._cookies

    def refresh(self) -> None:
        """Force refresh the session and cookies."""
        self._init_session()


class NSEDataFetcher:
    """Class to handle NSE data fetching with session management."""

    BASE_URL = "https://www.nseindia.com"
    CACHE_DIR = Path("cache")

    def __init__(self):
        """Initialize NSE data fetcher."""
        self.nse_session = NSESession()
        self.BASE_URL = self.nse_session.BASE_URL
        self.cookies = self.nse_session.cookies
        self.headers = self.nse_session.headers

        # Create cache directory if it doesn't exist
        self.CACHE_DIR.mkdir(exist_ok=True)

    def get_underlying_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Fetch underlying information from NSE API.
        Returns a dictionary containing indices and stock symbols.
        """
        try:
            print("Fetching underlying information...")
            response = self.nse_session.session.get(
                f"{self.BASE_URL}/api/underlying-information",
                headers=self.headers,
                cookies=self.cookies,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return {
                    # "indices": data["data"]["IndexList"],
                    "indices": [],
                    "stocks": data["data"]["UnderlyingList"],
                }

            return {"indices": [], "stocks": []}

        except Exception as e:
            print(f"Error fetching underlying information: {str(e)}")
            return {"indices": [], "stocks": []}

    def _get_cache_path(self, symbol: str) -> Path:
        """Get the cache file path for a symbol."""
        return self.CACHE_DIR / f"{symbol}.json"

    def _read_cache(self, symbol: str, expiry_date: str) -> Optional[pd.DataFrame]:
        """Read cached data for a symbol and expiry date."""
        cache_path = self._get_cache_path(symbol)
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)
                    if expiry_date in cache_data:
                        return pd.read_json(
                            StringIO(cache_data[expiry_date]),
                            orient="records",
                            convert_dates=["Date"],
                        )
            except Exception as e:
                print(f"Error reading cache: {e}")
        return None

    def _write_cache(self, symbol: str, expiry_date: str, data: pd.DataFrame) -> None:
        """Write data to cache."""
        cache_path = self._get_cache_path(symbol)

        # Read existing cache or create new
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)
            except json.JSONDecodeError:
                cache_data = {}
        else:
            cache_data = {}

        # Update cache with new data
        cache_data[expiry_date] = data.to_json(orient="records", date_format="iso")

        # Write updated cache
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)

    def _is_past_date(self, expiry_date: str) -> bool:
        """
        Determine if cache should be used based on expiry date.
        Returns False for current and future month expiries.
        """
        try:
            expiry = datetime.strptime(expiry_date, "%d-%b-%Y")
            today = datetime.now()

            # If expiry is in current month or future, don't use cache
            if (expiry.year, expiry.month) >= (today.year, today.month):
                return False
            return True
        except Exception as e:
            print(f"Error parsing expiry date: {e}")
            return False

    def get_futures_data(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        expiry_date: str,
        use_cache_for_future: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch futures data with automatic cache management.
        Always fetches fresh data for current and future month expiries.

        Args:
            symbol: Stock symbol (e.g., 'SBIN')
            from_date: Start date in DD-MM-YYYY format
            to_date: End date in DD-MM-YYYY format
            expiry_date: Expiry date in DD-MMM-YYYY format
            use_cache: Whether to use cached data if available (for past expiries only)
        """
        # Determine if we should use cache based on expiry date
        should_use_cache = self._is_past_date(expiry_date)

        if use_cache_for_future:
            should_use_cache = True

        # Check cache first if enabled and expiry is in the past
        if should_use_cache:
            cached_df = self._read_cache(symbol, expiry_date)
            if cached_df is not None:
                print(f"Using cached data for {symbol} expiry {expiry_date}")
                return cached_df

        # Fetch fresh data if:
        # 1. Cache is disabled
        # 2. Expiry is current/future month
        # 3. Cache miss for past expiry
        try:
            print("Fetching fresh data...")
            url = (
                f"{self.BASE_URL}/api/historical/fo/derivatives"
                f"?&from={from_date}&to={to_date}"
                f"&expiryDate={expiry_date}"
                f"&instrumentType=FUTSTK&symbol={symbol}"
            )

            # Update headers for this specific request
            request_headers = self.headers.copy()
            request_headers.update(
                {
                    "Referer": (
                        f"{self.BASE_URL}/get-quotes/derivatives?symbol={symbol}"
                    ),
                    "path": (
                        f"/api/historical/fo/derivatives?from={from_date}"
                        f"&to={to_date}&expiryDate={expiry_date}"
                        f"&instrumentType=FUTSTK&symbol={symbol}"
                    ),
                }
            )

            response = self.nse_session.session.get(
                url, headers=request_headers, cookies=self.cookies, timeout=30
            )

            print(response.status_code)

            response.raise_for_status()

            try:
                data = response.json()
            except ValueError as e:
                print("Failed to parse JSON response")
                print(f"Error: {str(e)}")
                return None

            if isinstance(data, dict) and "data" in data:
                df = pd.DataFrame(data["data"])

                if df.empty:
                    print(f"No data found for {symbol} expiry {expiry_date}")
                    self._write_cache(symbol, expiry_date, df)
                    return df

                # Rename columns to standard format
                column_mapping = {
                    "FH_TIMESTAMP": "Date",
                    "FH_OPENING_PRICE": "Open",
                    "FH_HIGH_PRICE": "High",
                    "FH_LOW_PRICE": "Low",
                    "FH_CLOSING_PRICE": "Close",
                    "FH_TOT_TRADED_QTY": "Volume",
                    "FH_OPEN_INT": "Open Interest",
                    "FH_SETTLE_PRICE": "Settlement Price",
                }

                # Convert numeric columns
                numeric_columns = [
                    "FH_OPENING_PRICE",
                    "FH_HIGH_PRICE",
                    "FH_LOW_PRICE",
                    "FH_CLOSING_PRICE",
                    "FH_TOT_TRADED_QTY",
                    "FH_OPEN_INT",
                    "FH_SETTLE_PRICE",
                ]

                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(
                            df[col].str.replace(",", ""), errors="coerce"
                        )

                # Rename columns that exist in the DataFrame
                existing_columns = {
                    old: new for old, new in column_mapping.items() if old in df.columns
                }
                df = df.rename(columns=existing_columns)
                # Convert date column
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%Y")
                # Sort by date
                df = df.sort_values("Date")
                print(
                    f"Successfully fetched {len(df)} records for {symbol} "
                    f"expiry {expiry_date}"
                )

                if df is not None and not df.empty:
                    self._write_cache(symbol, expiry_date, df)
                    return df

                return None

            print(f"No data found for {symbol} expiry {expiry_date}")
            return None

        except Exception as e:
            print(f"Error fetching futures data for {symbol}: {str(e)}")
            return None
