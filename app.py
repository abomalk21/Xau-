import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta

# --- الإعدادات الأساسية ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.set_page_config(page_title="XAU Pro Radar", layout="wide")

@st.cache_data(ttl=12) # تحديث سريع جداً لمراقبة الاختراقات
def get_data():
    try:
        df = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=True)
        if df.empty: return None
        df.index = df.index.tz_convert(ny_tz)
        return df.dropna()
    except: return None

st.title("🏆 XAU Pro Radar")
data = get_data()

if data is not None and len(data) > 2:
    now_ny = datetime.now(ny_tz)
    last_p = float(data['Close'].iloc[-1])
    
    # 1. حساب المستويات الأساسية
    mid_df = data[data.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_val = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(data['Open'].iloc[0])
    
    asia = data.between_time("20:00", "00:00")
    ah, al = (float(asia['High'].max()), float(asia['Low'].min())) if not asia.empty else (0.0, 0.0)
    
    london = data.between_time("02:00", "05:00")
    lh, ll = (float(london['High'].max()), float(london['Low'].min())) if not london.empty else (0.0, 0.0)

    # 2. نظام تنبيهات اختراق المستويات (Breakout Alerts)
    st.subheader("🚨 Level Breakout Alerts")
    
    alert_col1, alert_col2 = st.columns(2)
    
    with alert_col1:
        # تنبيهات لندن
        if lh > 0 and last_p > lh:
            st.error(f"🔥 LONDON HIGH BROKEN! Price: {last_p:.2f} > {lh:.2f}")
        elif ll > 0 and last_p < ll:
            st.success(f"🧊 LONDON LOW BROKEN! Price: {last_p:.2f} < {ll:.2f}")
        else:
            st.write("✅ Price within London Range")

    with alert_col2:
        # تنبيهات آسيا
        if ah > 0 and last_p > ah:
            st.error(f"🔥 ASIA HIGH BROKEN! Price: {last_p:.2f} > {ah:.2f}")
        elif al > 0 and last_p < al:
            st.success(f"🧊 ASIA LOW BROKEN! Price: {last_p:.2f} < {al:.2f}")
        else:
            st.write("✅ Price within Asia Range")

    st.markdown("---")

    # 3. مربع التوصية (بيع/شراء) بناءً على Midnight
    if last_p > mn_val:
        st.markdown(f"<div style='background-color:#ff4b4b; padding:20px; border-radius:10px; text-align:center;'> <h2 style='color:white;'>🔴 SELL SIGNAL</h2> <p style='color:white;'>Price is ABOVE Midnight ({mn_val:.2f})</p></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color:#28a745; padding:20px; border-radius:10px; text-align:center;'> <h2 style='color:white;'>🟢 BUY SIGNAL</h2> <p style='color:white;'>Price is BELOW Midnight ({mn_val:.2f})</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # 4. جدول المستويات الرقمية
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🇬🇧 London Session")
        st.metric("High (Target)", f"{lh:.2f}")
        st.metric("Low (Target)", f"{ll:.2f}")
    with col2:
        st.warning("🌏 Asia Session")
        st.metric("High (Target)", f"{ah:.2f}")
        st.metric("Low (Target)", f"{al:.2f}")
    with col3:
        st.metric("💰 Live Gold", f"{last_p:.2f}")
        rem_min = 14 - (now_ny.minute % 15)
        st.metric("⏳ Bar Ends", f"{rem_min:02d}:{59 - now_ny.second:02d}")

    # التوقيت السفلي
    st.write(f"🕒 NY Time: `{now_ny.strftime('%H:%M')}` | Baghdad: `{datetime.now(bg_tz).strftime('%H:%M')}`")

else:
    st.info("Searching for Live Data...")

if st.button('🔄 Refresh Digital Radar'): st.rerun()
