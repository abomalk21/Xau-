import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta

# --- الإعدادات الزمنية ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.set_page_config(page_title="XAU Bullet Radar", layout="wide")

# تقليل الـ TTL لضمان التحديث اللحظي الفعلي
@st.cache_data(ttl=2) 
def get_fast_data():
    try:
        # استخدام الرمز الفوري XAUUSD=X لتقليل الفجوة السعرية
        df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
        return df
    except Exception:
        return None

st.title("🏹 XAU Silver Bullet Radar")

data = get_fast_data()

if data is not None and not data.empty:
    now_ny = datetime.now(ny_tz)
    last_p = float(data['Close'].iloc[-1])
    # سعر افتتاح أول دقيقة في اليوم (Midnight Open)
    mn_val = float(data['Open'].iloc[0]) 

    # --- 1. التوصية المركزية (خلفية ملونة لسرعة اتخاذ القرار) ---
    if last_p > mn_val:
        st.markdown(f"<div style='background-color:#ff4b4b; padding:25px; border-radius:15px; text-align:center;'> <h1 style='color:white; margin:0;'>🔴 SELL SIGNAL</h1> <p style='color:white; font-size:20px;'>Price {last_p:.2f} is ABOVE Midnight {mn_val:.2f}</p></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color:#28a745; padding:25px; border-radius:15px; text-align:center;'> <h1 style='color:white; margin:0;'>🟢 BUY SIGNAL</h1> <p style='color:white; font-size:20px;'>Price {last_p:.2f} is BELOW Midnight {mn_val:.2f}</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- 2. عدادات السيلفر بوليت بالثواني (حاسمة للدخول) ---
    col_time1, col_time2 = st.columns(2)
    
    # تحديد نافذة السيلفر بوليت القادمة (10am أو 2pm NY)
    sb_windows = [10, 14]
    next_sb_hour = next((h for h in sb_windows if h > now_ny.hour), 10)
    target_sb = now_ny.replace(hour=next_sb_hour, minute=0, second=0, microsecond=0)
    if next_sb_hour == 10 and now_ny.hour >= 14:
        target_sb += timedelta(days=1)
    
    time_diff = target_sb - now_ny
    h, m, s = str(time_diff).split(".")[0].split(":")

    with col_time1:
        st.metric("🏹 Time to Silver Bullet", f"{h}h {m}m {s}s")
    with col_time2:
        st.metric("💰 Spot Price (Live)", f"{last_p:.2f}")

    # --- 3. نظام التنبيهات المرئية لكسر المستويات ---
    st.markdown("### 🚨 Level Watch")
    # ملاحظة: هذه القيم ثابتة من بيانات الـ 15 دقيقة السابقة لتقليل الضغط
    # سنكتفي هنا بمراقبة السعر الحالي مقابل قمة وقاع اليوم
    day_high = float(data['High'].max())
    day_low = float(data['Low'].min())

    c1, c2 = st.columns(2)
    if last_p >= day_high:
        c1.error(f"🔥 Price at Day High: {day_high:.2f}")
    else:
        c1.info(f"High Target: {day_high:.2f}")
        
    if last_p <= day_low:
        c2.success(f"🧊 Price at Day Low: {day_low:.2f}")
    else:
        c2.info(f"Low Target: {day_low:.2f}")

    # المعلومات الزمنية السفلية
    st.write(f"🕒 **NY:** `{now_ny.strftime('%H:%M:%S')}` | **Baghdad:** `{datetime.now(bg_tz).strftime('%H:%M:%S')}`")

else:
    st.error("⚠️ Connection Lost. Retrying...")
    st.button("Force Reconnect")
    st.rerun()
