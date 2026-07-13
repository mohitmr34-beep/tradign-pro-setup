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

st.sidebar.markdown("---")
st.sidebar.write("### 📊 Strategy")
st.sidebar.write("• 9:20 Trap")
st.sidebar.write("• 9:25 Breakout")
st.sidebar.write("• AI Score")
st.sidebar.write("• Hedge Mode")

# =========================
# TITLE
# =========================
st.title("🤖 AI Trading System with Hedge Mode")
st.subheader(f"Symbol: {symbol}")

# =========================
# LOAD DATA (ROBUST)
# =========================
@st.cache_data(ttl=60)
def load_data(sym):
    try:
        # Try 5m
        df = yf.download(sym, period="5d", interval="5m", progress=False)
        if df is not None and not df.empty:
            return df, "5m"

        # Fallback 15m
        df = yf.download(sym, period="5d", interval="15m", progress=False)
        if df is not None and not df.empty:
            return df, "15m"

        # Fallback daily
        df = yf.download(sym, period="1mo", interval="1d", progress=False)
        if df is not None and not df.empty:
            return df, "1d"

        return None, None

    except:
        return None, None

df, timeframe = load_data(symbol)

if df is None or df.empty:
    st.error("❌ Data not available from Yahoo. Try during market hours.")
    st.stop()

# =========================
# SHOW DATA INFO
# =========================
if timeframe != "5m":
    st.warning(f"⚠️ Using {timeframe} data (5m not available)")

df.dropna(inplace=True)

if len(df) < 20:
    st.warning("Not enough data yet.")
    st.stop()

st.write("🕒 Last Data Time:", df.index[-1])

# =========================
# INDICATORS
# =========================
df['EMA50'] = df['Close'].ewm(span=50).mean()
df['EMA200'] = df['Close'].ewm(span=200).mean()

df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

rsi = RSIIndicator(df['Close'], window=14)
df['RSI'] = rsi.rsi()

df['Vol_Avg'] = df['Volume'].rolling(5).mean()

# =========================
# LAST 2 CANDLES
# =========================
c1 = df.iloc[-2]
c2 = df.iloc[-1]

# =========================
# CONDITIONS
# =========================
uptrend = c2['EMA50'] > c2['EMA200']
downtrend = c2['EMA50'] < c2['EMA200']

gap_up = c2['Open'] > c1['Close']
gap_down = c2['Open'] < c1['Close']

c1_red = c1['Close'] < c1['Open']
c1_green = c1['Close'] > c1['Open']

vol_spike_1 = c1['Volume'] > c1['Vol_Avg']
vol_spike_2 = c2['Volume'] > c2['Vol_Avg']

break_high = c2['High'] > c1['High']
break_low = c2['Low'] < c1['Low']

above_vwap = c2['Close'] > c2['VWAP']
below_vwap = c2['Close'] < c2['VWAP']

rsi_val = c2['RSI']

# =========================
# SIDEWAYS
# =========================
sideways = (45 < rsi_val < 55) and abs(c2['EMA50'] - c2['EMA200']) < 1

# =========================
# AI SCORE
# =========================
score = 0

if uptrend or downtrend:
    score += 20
if gap_up or gap_down:
    score += 15
if c1_red or c1_green:
    score += 15
if vol_spike_1:
    score += 10
if above_vwap or below_vwap:
    score += 10
if rsi_val > 50 or rsi_val < 50:
    score += 10
if break_high or break_low:
    score += 10
if vol_spike_2:
    score += 10
if sideways:
    score -= 30

# =========================
# SIGNAL
# =========================
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

# =========================
# DISPLAY
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("AI Score", score)
col2.metric("Signal", signal)
col3.metric("RSI", round(rsi_val, 2))

# =========================
# CONDITIONS
# =========================
st.subheader("📊 Conditions")

st.write({
    "Uptrend": uptrend,
    "Downtrend": downtrend,
    "Gap Up": gap_up,
    "Gap Down": gap_down,
    "Candle Red": c1_red,
    "Candle Green": c1_green,
    "Vol Spike 1": vol_spike_1,
    "Vol Spike 2": vol_spike_2,
    "Break High": break_high,
    "Break Low": break_low,
    "Above VWAP": above_vwap,
    "Below VWAP": below_vwap,
    "Sideways": sideways
})

# =========================
# CHART
# =========================
st.subheader("📈 Chart")
st.line_chart(df[['Close', 'EMA50', 'EMA200', 'VWAP']])
