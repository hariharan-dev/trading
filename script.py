import yfinance as yf
import pandas as pd
import os
import pickle

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json


# List of NSE stocks (you can use a predefined list or fetch it from an API)
nse_stocks = [
    'ABB.NS',
    'ACC.NS',
    'APLAPOLLO.NS',
    'AUBANK.NS',
    'ADANIENSOL.NS',
    'ADANIENT.NS',
    'ADANIGREEN.NS',
    'ADANIPORTS.NS',
    'ADANIPOWER.NS',
    'ATGL.NS',
    'ABCAPITAL.NS',
    'ABFRL.NS',
    'ALKEM.NS',
    'AMBUJACEM.NS',
    'APOLLOHOSP.NS',
    'APOLLOTYRE.NS',
    'ASHOKLEY.NS',
    'ASIANPAINT.NS',
    'ASTRAL.NS',
    'AUROPHARMA.NS',
    'DMART.NS',
    'AXISBANK.NS',
    'BSE.NS',
    'BAJAJ-AUTO.NS',
    'BAJFINANCE.NS',
    'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS',
    'BALKRISIND.NS',
    'BANDHANBNK.NS',
    'BANKBARODA.NS',
    'BANKINDIA.NS',
    'MAHABANK.NS',
    'BDL.NS',
    'BEL.NS',
    'BHARATFORG.NS',
    'BHEL.NS',
    'BPCL.NS',
    'BHARTIARTL.NS',
    'BHARTIHEXA.NS',
    'BIOCON.NS',
    'BOSCHLTD.NS',
    'BRITANNIA.NS',
    'CGPOWER.NS',
    'CANBK.NS',
    'CHOLAFIN.NS',
    'CIPLA.NS',
    'COALINDIA.NS',
    'COCHINSHIP.NS',
    'COFORGE.NS',
    'COLPAL.NS',
    'CONCOR.NS',
    'CUMMINSIND.NS',
    'DLF.NS',
    'DABUR.NS',
    'DELHIVERY.NS',
    'DIVISLAB.NS',
    'DIXON.NS',
    'DRREDDY.NS',
    'EICHERMOT.NS',
    'ESCORTS.NS',
    'EXIDEIND.NS',
    'NYKAA.NS',
    'FEDERALBNK.NS',
    'FACT.NS',
    'GAIL.NS',
    'GMRAIRPORT.NS',
    'GODREJCP.NS',
    'GODREJPROP.NS',
    'GRASIM.NS',
    'HCLTECH.NS',
    'HDFCAMC.NS',
    'HDFCBANK.NS',
    'HDFCLIFE.NS',
    'HAVELLS.NS',
    'HEROMOTOCO.NS',
    'HINDALCO.NS',
    'HAL.NS',
    'HINDPETRO.NS',
    'HINDUNILVR.NS',
    'HINDZINC.NS',
    'HUDCO.NS',
    'ICICIBANK.NS',
    'ICICIGI.NS',
    'ICICIPRULI.NS',
    'IDBI.NS',
    'IDFCFIRSTB.NS',
    'IRB.NS',
    'ITC.NS',
    'INDIANB.NS',
    'INDHOTEL.NS',
    'IOC.NS',
    'IOB.NS',
    'IRCTC.NS',
    'IRFC.NS',
    'IREDA.NS',
    'IGL.NS',
    'INDUSTOWER.NS',
    'INDUSINDBK.NS',
    'NAUKRI.NS',
    'INFY.NS',
    'INDIGO.NS',
    'JSWENERGY.NS',
    'JSWINFRA.NS',
    'JSWSTEEL.NS',
    'JINDALSTEL.NS',
    'JIOFIN.NS',
    'JUBLFOOD.NS',
    'KPITTECH.NS',
    'KALYANKJIL.NS',
    'KOTAKBANK.NS',
    'LTF.NS',
    'LICHSGFIN.NS',
    'LTIM.NS',
    'LT.NS',
    'LICI.NS',
    'LUPIN.NS',
    'MRF.NS',
    'LODHA.NS',
    'M&MFIN.NS',
    'M&M.NS',
    'MRPL.NS',
    'MANKIND.NS',
    'MARICO.NS',
    'MARUTI.NS',
    'MFSL.NS',
    'MAXHEALTH.NS',
    'MAZDOCK.NS',
    'MPHASIS.NS',
    'MUTHOOTFIN.NS',
    'NHPC.NS',
    'NLCINDIA.NS',
    'NMDC.NS',
    'NTPC.NS',
    'NESTLEIND.NS',
    'OBEROIRLTY.NS',
    'ONGC.NS',
    'OIL.NS',
    'PAYTM.NS',
    'OFSS.NS',
    'POLICYBZR.NS',
    'PIIND.NS',
    'PAGEIND.NS',
    'PATANJALI.NS',
    'PERSISTENT.NS',
    'PETRONET.NS',
    'PHOENIXLTD.NS',
    'PIDILITIND.NS',
    'POLYCAB.NS',
    'POONAWALLA.NS',
    'PFC.NS',
    'POWERGRID.NS',
    'PRESTIGE.NS',
    'PNB.NS',
    'RECLTD.NS',
    'RVNL.NS',
    'RELIANCE.NS',
    'SBICARD.NS',
    'SBILIFE.NS',
    'SJVN.NS',
    'SRF.NS',
    'MOTHERSON.NS',
    'SHREECEM.NS',
    'SHRIRAMFIN.NS',
    'SIEMENS.NS',
    'SOLARINDS.NS',
    'SONACOMS.NS',
    'SBIN.NS',
    'SAIL.NS',
    'SUNPHARMA.NS',
    'SUNDARMFIN.NS',
    'SUPREMEIND.NS',
    'SUZLON.NS',
    'TVSMOTOR.NS',
    'TATACHEM.NS',
    'TATACOMM.NS',
    'TCS.NS',
    'TATACONSUM.NS',
    'TATAELXSI.NS',
    'TATAMOTORS.NS',
    'TATAPOWER.NS',
    'TATASTEEL.NS',
    'TATATECH.NS',
    'TECHM.NS',
    'TITAN.NS',
    'TORNTPHARM.NS',
    'TORNTPOWER.NS',
    'TRENT.NS',
    'TIINDIA.NS',
    'UPL.NS',
    'ULTRACEMCO.NS',
    'UNIONBANK.NS',
    'UNITDSPR.NS',
    'VBL.NS',
    'VEDL.NS',
    'IDEA.NS',
    'VOLTAS.NS',
    'WIPRO.NS',
    'YESBANK.NS',
    'ZOMATO.NS',
    'ZYDUSLIFE.NS',
]  # Add more stocks


# Create stocks_cache directory if it doesn't exist
os.makedirs('stocks_cache', exist_ok=True)


def get_cached_stock_data(stock_symbol, days=50):
    cache_file = os.path.join('stocks_cache', f'{stock_symbol.replace(".","_")}_{days}d.pkl')
    
    # Try to load from cache file
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            print(f"Loading {stock_symbol} from cache")
            return pickle.load(f)
    
    # If not in cache, download and save
    stock_data = yf.download(stock_symbol, period=f"{days}d")
    with open(cache_file, 'wb') as f:
        pickle.dump(stock_data, f)
    
    return stock_data


def check_stable_price(stock_symbol, days=50):
    stock_data = get_cached_stock_data(stock_symbol, days)
    
    # Calculate daily percentage change and take absolute value
    stock_data['Pct_Change'] = stock_data['Close'].pct_change().abs() * 100
    
    # Check if the max change is within 5%
    max_change = stock_data['Pct_Change'].max()
    
    return {
        'symbol': stock_symbol,
        'max_change': max_change,
        'is_stable': max_change <= 5,
        'avg_daily_change': stock_data['Pct_Change'].mean()
    }


# nse_stocks = nse_stocks[:1]

# Find stable stocks
stable_stocks = [
    stock for stock in nse_stocks 
    if check_stable_price(stock)['is_stable']
]
print("Stocks that haven't moved more than 5% in any single day:", stable_stocks)