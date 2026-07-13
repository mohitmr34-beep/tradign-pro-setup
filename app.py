import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator

st.set_page_config(page_title="AI Trading System", layout="wide")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Settings")

mode = st.sidebar.radio("Select Mode", ["Live Trading", "Backtest"])

market = st.sidebar.selectbox(
    "Select Market",
    ["NIFTY", "BANKNIFTY", "CUSTOM"]
)

if market == "NIFTY":
    symbol = "NIFTYBEES.NS"
elif market == "BANKNIFTY":
    symbol = "BANKBEES.NS"
else:
    symbol = st.sidebar.text_input("Enter Symbol", "RELIANCE.NS")

# =========================
# TITLE
# =========================
st.title("🤖 AI Trading System with Hedge Mode")
st.subheader(f"{mode} | Symbol: {symbol}")

# =========================
# DATA LOADER
# =========================
@st.cache_data(ttl=60)
def load_live(sym):
    try:
        df = yf.download(sym, period="5d", interval="5m", progress=False)
        if df.empty:
            df = yf.download(sym, period="5d", interval="15m", progress=False)
        return df
    except:
        return None

@st.cache_data
def load_backtest(sym):
    return yf.download(sym, period="1y", interval="15m", progress=False)

# =========================
# LOAD BASED ON MODE
# =========================
if mode == "Live Trading":
    df = load_live(symbol)
else:
    df = load_backtest(symbol)

if df is None or df.empty:
    st.error("❌ Data not available")
    st.stop()

df.dropna(inplace=True)

# =========================
# INDICATORS
# =========================
df['EMA50'] = df['Close'].ewm(span=50).mean()
df['EMA200'] = df['Close'].ewm(span=200).mean()

df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
df['Vol_Avg'] = df['Volume'].rolling(5).mean()

# =========================
# 🔴 LIVE MODE
# =========================
if mode == "Live Trading":

    if len(df) < 20:
        st.warning("Not enough data")
        st.stop()

    c1 = df.iloc[-2]
    c2 = df.iloc[-1]

    uptrend = c2['EMA50'] > c2['EMA200']
    downtrend = c2['EMA50'] < c2['EMA200']

    gap_up = c2['Open'] > c1['Close']
    gap_down = c2['Open'] < c1['Close']

    c1_red = c1['Close'] < c1['Open']
    c1_green = c1['Close'] > c1['Open']

    vol1 = c1['Volume'] > c1['Vol_Avg']
    vol2 = c2['Volume'] > c2['Vol_Avg']

    break_high = c2['High'] > c1['High']
    break_low = c2['Low'] < c1['Low']

    rsi = c2['RSI']

    sideways = (45 < rsi < 55)

    score = 0
    score += 20 if uptrend or downtrend else 0
    score += 15 if gap_up or gap_down else 0
    score += 15 if c1_red or c1_green else 0
    score += 10 if vol1 else 0
    score += 10 if vol2 else 0
    score += 10 if break_high or break_low else 0
    score += 10 if rsi else 0
    score -= 30 if sideways else 0

    signal = "WAIT"

    if sideways:
        signal = "🛡️ HEDGE MODE"
    elif score >= 80:
        if uptrend and gap_down and c1_red and break_high:
            signal = "🔥 STRONG BUY"
        elif downtrend and gap_up and c1_green and break_low:
            signal = "🔥 STRONG SELL"
        else:
            signal = "HIGH PROBABILITY"
    elif score >= 65:
        signal = "⚡ MODERATE"

    col1, col2, col3 = st.columns(3)
    col1.metric("AI Score", score)
    col2.metric("Signal", signal)
    col3.metric("RSI", round(rsi, 2))

# =========================
# 📊 BACKTEST MODE
# =========================
else:

    results = []

    for i in range(10, len(df)-1):

        c1 = df.iloc[i-1]
        c2 = df.iloc[i]

        uptrend = c2['EMA50'] > c2['EMA200']
        downtrend = c2['EMA50'] < c2['EMA200']

        gap_up = c2['Open'] > c1['Close']
        gap_down = c2['Open'] < c1['Close']

        c1_red = c1['Close'] < c1['Open']
        c1_green = c1['Close'] > c1['Open']

        break_high = c2['High'] > c1['High']
        break_low = c2['Low'] < c1['Low']

        rsi = c2['RSI']

        # BUY
        if uptrend and gap_down and c1_red and break_high and rsi > 50:
            entry = c2['Close']
            exit_price = df.iloc[i+1]['Close']
            results.append(exit_price - entry)

        # SELL
        elif downtrend and gap_up and c1_green and break_low and rsi < 50:
            entry = c2['Close']
            exit_price = df.iloc[i+1]['Close']
            results.append(entry - exit_price)

    if len(results) > 0:
        trades = len(results)
        wins = len([r for r in results if r > 0])
        win_rate = (wins / trades) * 100
        profit = sum(results)

        st.subheader("📊 Backtest Results")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Trades", trades)
        col2.metric("Win Rate %", round(win_rate, 2))
        col3.metric("Total Profit", round(profit, 2))

    else:
        st.warning("No trades found")

# =========================
# CHART
# =========================
st.subheader("📈 Chart")
st.line_chart(df[['Close', 'EMA50', 'EMA200']])
