import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# --- الإعدادات ---
ny_tz = pytz.timezone('America/New_York')

st.set_page_config(page_title="XAU Ultra-Live", layout="wide")

@st.cache_data(ttl=5) # تحديث كل 5 ثوانٍ لضمان الدقة
def get_ultra_live_data():
    try:
        # استخدام رمز XAUUSD=X لتقليل الفرق مع المنصة
        df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
        if df.empty: return None
        return df
    except: return None

data = get_ultra_live_data()

if data is not None:
    last_p = float(data['Close'].iloc[-1])
    # هنا نستخدم سعر الافتتاح لأول دقيقة في اليوم كمرجع لـ Midnight
    mn_val = float(data['Open'].iloc[0]) 

    # --- مربع الإشارة الفورية ---
    if last_p > mn_val:
        st.markdown(f"<div style='background-color:#ff4b4b; padding:30px; border-radius:15px; text-align:center;'> <h1 style='color:white;'>🚨 SELL NOW (Ultra-Live)</h1> <h3 style='color:white;'>Price {last_p:.2f} > Midnight {mn_val:.2f}</h3></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color:#28a745; padding:30px; border-radius:15px; text-align:center;'> <h1 style='color:white;'>🚀 BUY NOW (Ultra-Live)</h1> <h3 style='color:white;'>Price {last_p:.2f} < Midnight {mn_val:.2f}</h3></div>", unsafe_allow_html=True)

    st.metric("📊 Live XAU/USD", f"{last_p:.2f}")
    st.write("⚠️ *Note: Data syncs every 5 seconds to match your broker.*")
