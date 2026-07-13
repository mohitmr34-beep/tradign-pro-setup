# 🤖 AI Trading System with Hedge Mode

This is a **Streamlit-based intraday trading app** that uses a rule-based AI scoring system to generate **BUY / SELL / WAIT / HEDGE** signals based on market conditions.

---

## 🚀 Features

- 📊 9:20 Opening Trap Strategy
- ⏰ 9:25 Breakout Confirmation
- 📈 VWAP + RSI + Volume Analysis
- 🤖 AI Score (0–100)
- 🔥 Trade Strength Classification
- ⚠️ Sideways Market Detection
- 🛡️ Hedge Mode Suggestion
- 📉 Live Chart with EMA & VWAP

---

## 🧠 Strategy Logic

### ✅ BUY Setup
- Uptrend (EMA 50 > EMA 200)
- Gap Down
- 9:20 Red Candle (Sell Trap)
- Break of 9:20 High
- Price above VWAP
- RSI > 50
- Volume spike (9:20 + 9:25)

---

### ❌ SELL Setup
- Downtrend (EMA 50 < EMA 200)
- Gap Up
- 9:20 Green Candle (Buy Trap)
- Break of 9:20 Low
- Price below VWAP
- RSI < 50
- Volume spike (9:20 + 9:25)

---

### ⚠️ Sideways Market (HEDGE MODE)
- RSI between 45–55
- EMA flat
- Low momentum

👉 Suggestion:
- Avoid breakout trades  
- Use range trading or options hedge (Iron Condor)

---

## 📊 AI Score System

| Score Range | Signal |
|------------|--------|
| 80 – 100 | 🔥 Strong Trade |
| 65 – 79  | ✅ Moderate Trade |
| 50 – 64  | ⚠️ Low Quality |
| < 50     | ❌ WAIT / HEDGE |

---

## 🛠️ Installation

### 1. Clone repo
```bash
git clone https://github.com/your-username/ai-trading-system.git
cd ai-trading-system
