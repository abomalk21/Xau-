import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import time

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Gold Radar Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 40px !important; color: #f1c40f !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 18px !important; color: #ffffff !important; }
    .stAlert { background-color: #1e2130; border: none; }
    </style>
    """, unsafe_allow_html=True)

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

def get_data():
    # سحب بيانات 3 أيام لضمان تغطية جلسة آسيا السابقة
    return yf.download("GC=F", period="3d", interval="1m", progress=False, auto_adjust=True)

def get_session_high_low(df, start_time, end_time, tz):
    try:
        df_tz = df.copy()
        df_tz.index = df_tz.index.tz_convert(tz)
        # تحديد اليوم الحالي أو السابق بناءً على الوقت
        session_data = df_tz.between_time(start_time, end_time)
        if not session_data.empty:
            # نأخذ آخر جلسة مكتملة أو جارية
            latest_day = session_data.index[-1].date()
            today_session = session_data[session_data.index.date == latest_day]
            return today_session['High'].max(), today_session['Low'].min()
    except:
        pass
    return 0.0, 0.0

def get_sb_status(current_ny):
    # تعريف فترات السيلفر بوليت بتوقيت نيويورك
    windows = [
        ("03:00", "04:00", "L"),
        ("10:00", "11:00", "NY am"),
        ("14:00", "15:00", "NY pm")
    ]
    
    for start_str, end_str, label in windows:
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()
        start_dt = datetime.combine(current_ny.date(), start).replace(tzinfo=ny_tz)
        end_dt = datetime.combine(current_ny.date(), end).replace(tzinfo=ny_tz)
        
        if start_dt <= current_ny <= end_dt:
            return f"🔥 ACTIVE: {label}", ""
        
        if current_ny < start_dt:
            diff = start_dt - current_ny
            total_mins = int(diff.total_seconds() / 60)
            return f"⏳ {label}", f"{total_mins // 60}h {total_mins % 60}m"
            
    # إذا انتهت كل جلسات اليوم، نبحث عن أول جلسة في اليوم التالي (لندن)
    next_london = datetime.combine(current_ny.date() + timedelta(days=1), datetime.strptime("03:00", "%H:%M").time()).replace(tzinfo=ny_tz)
    diff = next_london - current_ny
    total_mins = int(diff.total_seconds() / 60)
    return "⏳ L", f"{total_mins // 60}h {total_mins % 60}m"

st.title("🏆 رادار الذهب المطور")
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            df = get_data()
            if not df.empty:
                now_ny = datetime.now(ny_tz)
                now_bg = datetime.now(bg_tz)
                latest = df['Close'].iloc[-1].item()
                
                # 1. حساب Midnight Open (00:00 NY)
                m_data = df[df.index.tz_convert(ny_tz).date == now_ny.date()].between_time('00:00', '00:05')
                mn_open = m_data['Open'].iloc[0].item() if not m_data.empty else df['Open'].iloc[-1].item()
                
                # 2. حساب مستويات آسيا (20:00 - 00:00 NY) ولندن (02:00 - 05:00 NY)
                asia_h, asia_l = get_session_high_low(df, "20:00", "00:00", ny_tz)
                london_h, london_l = get_session_high_low(df, "02:00", "05:00", ny_tz)
                
                # --- العرض في الصفحة ---
                # الصف الأول: الساعات والسعر
                c1, c2, c3 = st.columns(3)
                c1.metric("🇮🇶 Baghdad", now_bg.strftime("%H:%M"))
                c2.metric("💰 Gold Price", f"{latest:.2f}")
                c3.metric("🇺🇸 New York", now_ny.strftime("%H:%M"))
                
                st.divider()
                
                # الصف الثاني: Midnight و العداد المطور
                c4, c5 = st.columns(2)
                sb_label, sb_time = get_sb_status(now_ny)
                c4.metric("🎯 Midnight Open", f"{mn_open:.2f}")
                c5.metric(f"⏰ Next: {sb_label}", sb_time if sb_time else "Now!")

                # الصف الثالث: بيانات آسيا ولندن (High/Low)
                st.markdown("### 📊 Session Liquidity (High/Low)")
                col_a1, col_a2, col_l1, col_l2 = st.columns(4)
                col_a1.metric("🌏 Asia High", f"{asia_h:.2f}")
                col_a2.metric("🌏 Asia Low", f"{asia_l:.2f}")
                col_l1.metric("🇬🇧 London High", f"{london_h:.2f}")
                col_l2.metric("🇬🇧 London Low", f"{london_l:.2f}")

                # إشارة الاتجاه
                if latest < mn_open:
                    st.success(f"📈 Direction: BUY (Price below Midnight)")
                else:
                    st.error(f"📉 Direction: SELL (Price above Midnight)")
                
                st.line_chart(df['Close'].tail(100))
        except Exception as e:
            st.warning(f"Updating data... ")
            
    time.sleep(60)
    st.rerun()
