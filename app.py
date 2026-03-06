import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import time

# إعداد واجهة التابلت الاحترافية
st.set_page_config(page_title="Gold Tracker Pro", layout="wide")

# تصميم الألوان والخطوط
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 50px !important; color: #f1c40f !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 22px !important; color: #ffffff !important; }
    .stAlert { background-color: #1e2130; border: none; }
    </style>
    """, unsafe_allow_html=True)

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

def get_data():
    return yf.download("GC=F", period="2d", interval="1m", progress=False, auto_adjust=True)

def get_countdown(current_ny, windows):
    upcoming = []
    for start_str, name in windows:
        start_time = datetime.strptime(start_str, "%H:%M").time()
        start_dt = datetime.combine(current_ny.date(), start_time).replace(tzinfo=ny_tz)
        if current_ny > (start_dt + timedelta(hours=1)):
            start_dt += timedelta(days=1)
        diff = start_dt - current_ny
        if timedelta(0) <= diff <= timedelta(seconds=0): return f"🔥 {name} نشطة!"
        if diff > timedelta(0): upcoming.append((diff, name))
    if upcoming:
        closest_diff, closest_name = min(upcoming)
        total_mins = int(closest_diff.total_seconds() / 60)
        return f"⏳ {closest_name}: {total_mins // 60}س {total_mins % 60}د"
    return "😴 انتظار"

st.title("🏆 رادار الذهب - Silver Bullet")
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            df = get_data()
            if not df.empty:
                now_ny = datetime.now(ny_tz)
                now_bg = datetime.now(bg_tz)
                latest = df['Close'].iloc[-1].item()
                
                # حساب منتصف الليل
                m_data = df[df.index.tz_convert(ny_tz).date == now_ny.date()].between_time('00:00', '00:05')
                mn_open = m_data['Open'].iloc[0].item() if not m_data.empty else df['Open'].iloc[0].item()
                
                # صف المعلومات الرئيسي
                c1, c2, c3 = st.columns(3)
                c1.metric("🇮🇶 بغداد", now_bg.strftime("%H:%M"))
                c2.metric("💰 الذهب الآن", f"{latest:.2f}")
                c3.metric("🇺🇸 نيويورك", now_ny.strftime("%H:%M"))
                
                st.divider()
                
                # العداد وحالة الاتجاه
                c4, c5 = st.columns(2)
                countdown = get_countdown(now_ny, [("03:00", "لندن"), ("10:00", "NY AM"), ("14:00", "NY PM")])
                c4.metric("🎯 هدف منتصف الليل", f"{mn_open:.2f}")
                c5.metric("⏰ التوقيت القادم", countdown)
                
                if latest < mn_open:
                    st.success(f"📈 الاتجاه: شراء (السعر تحت {mn_open:.2f})")
                else:
                    st.error(f"📉 الاتجاه: بيع (السعر فوق {mn_open:.2f})")
                
                st.line_chart(df['Close'].tail(100))
        except:
            st.warning("جاري محاولة تحديث البيانات...")
            
    time.sleep(60)
    st.rerun()
