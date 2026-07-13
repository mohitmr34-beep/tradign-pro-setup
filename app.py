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

index_option = st.sidebar.selectbox(
    "Select Market",
    ["NIFTY", "BANKNIFTY", "CUSTOM"]
)

if index_option == "NIFTY":
    symbol = "NIFTYBEES.NS"
elif index_option == "BANKNIFTY":
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
# LOAD DATA
# =========================
@st.cache_data(ttl=60)
def load_data(sym):
    try:
        df = yf.download(sym, period="5d", interval="5m", progress=False)
        if df.empty:
            return None
        return df
    except:
        return None

df = load_data(symbol)

# fallback if needed
if df is None or df.empty:
    st.warning("⚠️ Primary data failed. Trying fallback...")
    df = load_data("NIFTYBEES.NS")

if df is None or df.empty:
    st.error("❌ Data not available. Try later.")
    st.stop()

df.dropna(inplace=True)

# =========================
# DATA CHECK
# =========================
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
c920 = df.iloc[-2]
c925 = df.iloc[-1]

# =========================
# CONDITIONS
# =========================
uptrend = c925['EMA50'] > c925['EMA200']
downtrend = c925['EMA50'] < c925['EMA200']

gap_up = c925['Open'] > c920['Close']
gap_down = c925['Open'] < c920['Close']

c920_red = c920['Close'] < c920['Open']
c920_green = c920['Close'] > c920['Open']

vol_spike_920 = c920['Volume'] > c920['Vol_Avg']
vol_spike_925 = c925['Volume'] > c925['Vol_Avg']

break_high = c925['High'] > c920['High']
break_low = c925['Low'] < c920['Low']

above_vwap = c925['Close'] > c925['VWAP']
below_vwap = c925['Close'] < c925['VWAP']

rsi_val = c925['RSI']

# =========================
# SIDEWAYS
# =========================
sideways = (45 < rsi_val < 55) and abs(c925['EMA50'] - c925['EMA200']) < 1

# =========================
# AI SCORE
# =========================
score = 0

if uptrend or downtrend:
    score += 20

if gap_up or gap_down:
    score += 15

if c920_red or c920_green:
    score += 15

if vol_spike_920:
    score += 10

if above_vwap or below_vwap:
    score += 10

if rsi_val > 50 or rsi_val < 50:
    score += 10

if break_high or break_low:
    score += 10

if vol_spike_925:
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
    if uptrend and gap_down and c920_red and break_high:
        signal = "🔥 STRONG BUY"
    elif downtrend and gap_up and c920_green and break_low:
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
    "920 Red": c920_red,
    "920 Green": c920_green,
    "Vol Spike 920": vol_spike_920,
    "Vol Spike 925": vol_spike_925,
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
