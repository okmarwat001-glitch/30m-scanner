import ccxt
import streamlit as st

# Binance initialize karne ka naya tareeqa (Cloud Friendly)
try:
    exchange = ccxt.binance({
        'urls': {
            'api': {
                'public': 'https://api3.binance.com/api/v3',  # Alternative domain jo cloud par block nahi hota
            },
        },
        'options': {
            'adjustForTimeDifference': True,
            'recvWindow': 60000,
        },
        'timeout': 30000,
    })
    
    # Check karne ke liye ke markets load ho rahi hain ya nahi
    exchange.load_markets()
    
except Exception as e:
    st.error(f"Binance connection error: {e}")
    # Agar phir bhi issue aaye, toh backup ke taur par sirf MEXC/Bitget chalne do taaki app crash na ho
