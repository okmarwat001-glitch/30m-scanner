import streamlit as st
import ccxt
import pandas as pd
import time

# Page layout configuration
st.set_page_config(page_title="30m Crypto Breakout Scanner", layout="wide")
st.title("🚀 30m Candle Breakout & Bullish Close Scanner")
st.write("Binance aur MEXC Spot markets ke real-time breakouts scan karein.")

# Initialize exchanges
@st.cache_resource
def init_exchanges():
    return {
        'binance': ccxt.binance({'enableRateLimit': True}),
        'mexc': ccxt.mexc({'enableRateLimit': True})
    }

exchanges = init_exchanges()

# Function to fetch USDT spot markets
def get_spot_pairs(exchange_obj):
    try:
        markets = exchange_obj.load_markets()
        pairs = []
        for symbol, market in markets.items():
            # Sirf active, spot aur USDT pairs select karne k liye
            if market['spot'] and market['active'] and symbol.endswith('/USDT'):
                # Fan tokens or leveraged tokens filter out krne k liye simple check
                if any(x in symbol for x in ['BEAR', 'BULL', 'UP', 'DOWN']):
                    continue
                pairs.append(symbol)
        return pairs
    except Exception as e:
        st.error(f"Error loading markets: {e}")
        return []

# Breakout and Bullish Close Detection Logic
def check_breakout(exchange_obj, symbol):
    try:
        # Pichle 30 candles fetch krte hain historical high nikalne k liye
        ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe='30m', limit=30)
        if len(ohlcv) < 5:
            return None
        
        # DataFrame conversion
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Last closed candle (index -2) aur uski pichli history
        # Index -1 running candle hoti hai, is liye hum complete closed candle (-2) check krenge
        last_closed = df.iloc[-2]
        previous_candles = df.iloc[:-2] # Baqi pichli saari candles
        
        # Recent Resistance / High point calculation (Pichli 20 candles ka max high)
        recent_high = previous_candles['high'].tail(20).max()
        
        # Condition 1: Current closed candle ka Close pichle high se upar ho (Breakout)
        # Condition 2: Candle green (Bullish) close hui ho -> Close > Open
        if last_closed['close'] > recent_high and last_closed['close'] > last_closed['open']:
            breakout_pct = ((last_closed['close'] - recent_high) / recent_high) * 100
            return {
                'Symbol': symbol,
                'Close Price': last_closed['close'],
                'Recent High': recent_high,
                'Breakout Amnt (%)': round(breakout_pct, 2),
                'Volume': last_closed['volume']
            }
    except Exception:
        return None
    return None

# UI Sidebar Controls
st.sidebar.header("Scanner Settings")
scan_trigger = st.sidebar.button("Start Scan 🔍", use_container_width=True)

if scan_trigger:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Fetching trading pairs from Binance & MEXC...")
    binance_pairs = get_spot_pairs(exchanges['binance'])
    mexc_pairs = get_spot_pairs(exchanges['mexc'])
    
    # Duplicate prevention: Agar coin binance pe hai to mexc pe scan na ho
    scanned_base_currencies = set()
    final_scan_list = []
    
    for p in binance_pairs:
        base = p.split('/')[0]
        final_scan_list.append(('binance', p))
        scanned_base_currencies.add(base)
        
    for p in mexc_pairs:
        base = p.split('/')[0]
        if base not in scanned_base_currencies:
            final_scan_list.append(('mexc', p))
            scanned_base_currencies.add(base)
            
    total_coins = len(final_scan_list)
    st.sidebar.info(f"Total Unique Pairs to Scan: {total_coins}")
    
    breakout_signals = []
    
    # Scanning Loop
    for idx, (ex_name, symbol) in enumerate(final_scan_list):
        status_text.text(f"Scanning {idx+1}/{total_coins}: {symbol} on {ex_name.upper()}")
        progress_bar.progress((idx + 1) / total_coins)
        
        res = check_breakout(exchanges[ex_name], symbol)
        if res:
            res['Exchange'] = ex_name.upper()
            # Dynamic TradingView Link generation
            tv_symbol = symbol.replace('/', '')
            res['Chart Link'] = f"https://www.tradingview.com/chart/?symbol={ex_name.upper()}:{tv_symbol}"
            breakout_signals.append(res)
            
        # Small delay to respect API rate limits
        time.sleep(0.05)
        
    status_text.text("Scanning Completed! 🎉")
    progress_bar.empty()
    
    # Display Results
    if breakout_signals:
        df_results = pd.DataFrame(breakout_signals)
        # Reordering columns for better view
        df_results = df_results[['Symbol', 'Exchange', 'Close Price', 'Recent High', 'Breakout Amnt (%)', 'Chart Link']]
        
        st.success(f"Dono exchanges ko mila kar **{len(df_results)}** coins breakout zone mein mile!")
        
        # Render table with active links
        st.dataframe(
            df_results,
            column_config={
                "Chart Link": st.column_config.LinkColumn("TradingView Chart")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("Filhal koi bhi coin 30m candle par recent resistance break karke bullish close nahi hua.")