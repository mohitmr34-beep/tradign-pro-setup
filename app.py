import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator

st.set_page_config(page_title="AI Trading System PRO", layout="wide")

# =========================
# GLOBAL CACHE
# =========================
if "last_df" not in st.session_state:
    st.session_state.last_df = None

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Settings")

mode = st.sidebar.radio("Mode", ["Live Trading", "Backtest"])

market = st.sidebar.selectbox(
    "Market",
    ["NIFTY", "BANKNIFTY", "CUSTOM"]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["5m", "15m", "1d"]
)

# =========================
# SMART SYMBOL (KEY FIX)
# =========================
def get_symbol(market, timeframe):
    if market == "NIFTY":
        return "RELIANCE.NS" if timeframe != "1d" else "^NSEI"
    elif market == "BANKNIFTY":
        return "HDFCBANK.NS" if timeframe != "1d" else "^NSEBANK"
    else:
        return st.sidebar.text_input("Symbol", "RELIANCE.NS")

symbol = get_symbol(market, timeframe)

# =========================
# TITLE
# =========================
st.title("🤖 AI Trading System PRO")
st.subheader(f"{mode} | {symbol} | {timeframe}")

# =========================
# DATA ENGINE (PRO)
# =========================
def get_period(tf):
    if tf == "1d":
        return "1y"
    elif tf == "15m":
        return "10d"
    else:
        return "5d"

def fetch(sym, tf):
    try:
        return yf.download(sym, period=get_period(tf), interval=tf, progress=False)
    except:
        return None

def load_data(symbol, timeframe):

    # 1. PRIMARY
    df = fetch(symbol, timeframe)
    if df is not None and not df.empty:
        st.session_state.last_df = df
        return df, "LIVE", symbol

    # 2. FALLBACK
    for fb in ["RELIANCE.NS", "HDFCBANK.NS"]:
        df = fetch(fb, timeframe)
        if df is not None and not df.empty:
            st.session_state.last_df = df
            return df, "FALLBACK", fb

    # 3. CACHE
    if st.session_state.last_df is not None:
        return st.session_state.last_df, "CACHED", symbol

    return None, "FAILED", symbol


df, status, used_symbol = load_data(symbol, timeframe)

# =========================
# STATUS DISPLAY
# =========================
if status == "LIVE":
    st.success(f"🟢 Live Data: {used_symbol}")
elif status == "FALLBACK":
    st.warning(f"🟡 Fallback Data: {used_symbol}")
elif status == "CACHED":
    st.info("🔵 Using Cached Data")
else:
    st.error("❌ No data available")
    st.stop()

# =========================
# CLEAN DATA
# =========================
df = df.dropna()

if "Volume" in df.columns:
    df["Volume"] = df["Volume"].fillna(0)

if len(df) < 50:
    st.warning("⚠️ Limited data")

st.write("🕒 Last Data:", df.index[-1])

# =========================
# INDICATORS
# =========================
df['EMA50'] = df['Close'].ewm(span=50).mean()
df['EMA200'] = df['Close'].ewm(span=200).mean()
df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
df['Vol_Avg'] = df['Volume'].rolling(5).mean()

# =========================
# LIVE MODE
# =========================
if mode == "Live Trading":

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
    score += 10
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
        signal = "⚡ MODERATE TRADE"

    col1, col2, col3 = st.columns(3)
    col1.metric("AI Score", score)
    col2.metric("Signal", signal)
    col3.metric("RSI", round(rsi, 2))

# =========================
# BACKTEST
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

        if uptrend and gap_down and c1_red and break_high and rsi > 50:
            results.append(df.iloc[i+1]['Close'] - c2['Close'])

        elif downtrend and gap_up and c1_green and break_low and rsi < 50:
            results.append(c2['Close'] - df.iloc[i+1]['Close'])

    if results:
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
