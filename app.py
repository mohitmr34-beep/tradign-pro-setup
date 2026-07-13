import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator

st.set_page_config(page_title="AI Trading System", layout="wide")

# =========================
# SIDEBAR SETTINGS
# =========================
st.sidebar.title("⚙️ Settings")

mode = st.sidebar.radio("Mode", ["Live Trading", "Backtest"])

market = st.sidebar.selectbox(
    "Market",
    ["NIFTY", "BANKNIFTY", "CUSTOM"]
)

# ✅ STABLE SYMBOLS (FIXED)
if market == "NIFTY":
    symbol = "^NSEI"
elif market == "BANKNIFTY":
    symbol = "^NSEBANK"
else:
    symbol = st.sidebar.text_input("Symbol", "RELIANCE.NS")

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["5m", "15m", "1d"]
)

st.sidebar.markdown("---")
st.sidebar.write("### 📊 Strategy")
st.sidebar.write("• 9:20 Trap Logic")
st.sidebar.write("• 9:25 Breakout")
st.sidebar.write("• AI Score")
st.sidebar.write("• Hedge Mode")

# =========================
# TITLE
# =========================
st.title("🤖 AI Trading System with Hedge Mode")
st.subheader(f"{mode} | {symbol} | {timeframe}")

# =========================
# DATA LOADER (FINAL FIX)
# =========================
@st.cache_data(ttl=60)
def load_data(sym, tf):
    try:
        # ===== SMART PERIOD =====
        if tf == "1d":
            period = "1y"
        elif tf == "15m":
            period = "10d"
        elif tf == "5m":
            period = "5d"
        else:
            period = "1mo"

        df = yf.download(sym, period=period, interval=tf, progress=False)

        # ===== MULTI FALLBACK =====
        if df is None or df.empty:
            st.warning(f"⚠️ {sym} failed. Trying fallback...")

            fallback_symbols = [
                "^NSEI",
                "^NSEBANK",
                "RELIANCE.NS"
            ]

            for fb in fallback_symbols:
                df = yf.download(fb, period=period, interval=tf, progress=False)
                if df is not None and not df.empty:
                    st.info(f"✅ Using fallback: {fb}")
                    return df

            return None

        return df

    except Exception as e:
        st.error(f"Error: {e}")
        return None


# =========================
# LOAD DATA
# =========================
df = load_data(symbol, timeframe)

# ===== SAFE HANDLING =====
if df is None or df.empty:
    st.warning("⚠️ Data not available. Try switching timeframe.")
    st.stop()

df = df.dropna()

# Fix Yahoo volume bug
if "Volume" in df.columns:
    df["Volume"] = df["Volume"].fillna(0)

if len(df) < 50:
    st.warning("⚠️ Not enough candles for strategy")
    st.stop()

st.write("🕒 Last Data:", df.index[-1])

# =========================
# INDICATORS
# =========================
df['EMA50'] = df['Close'].ewm(span=50).mean()
df['EMA200'] = df['Close'].ewm(span=200).mean()
df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
df['Vol_Avg'] = df['Volume'].rolling(5).mean()

# =========================
# 🔴 LIVE MODE
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
