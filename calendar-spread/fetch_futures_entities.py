"""
Script to fetch and list all futures entities available on NSE India.
"""

from typing import Dict, List

from nse_api import NSEDataFetcher


def get_all_futures_entities() -> Dict[str, List[str]]:
    """
    Fetches and categorizes all futures entities available on NSE.

    Returns:
        Dictionary containing categorized futures entities
    """
    print("Starting to fetch all futures entities...")
    nse = NSEDataFetcher()
    futures_entities = nse.get_underlying_info()
    print("Completed fetching all futures entities")
    return futures_entities


def main() -> None:
    """
    Main function to fetch and display all futures entities.
    """
    print("Fetching futures entities from NSE India...")

    futures_entities = get_all_futures_entities()

    print("\nAvailable Index Futures:")
    print("-" * 30)
    for index in futures_entities["indices"]:
        print(f"- {index}")

    print("\nAvailable Stock Futures:")
    print("-" * 30)
    for stock in futures_entities["stocks"]:
        print(f"- {stock}")


if __name__ == "__main__":
    main()
