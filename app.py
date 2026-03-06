import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go # المكتبة الجديدة للشموع

# --- إعدادات الواجهة الاحترافية للتابلت ---
st.set_page_config(page_title="Gold Radar Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 38px !important; color: #f1c40f !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 16px !important; color: #ffffff !important; }
    .stAlert { background-color: #1e2130; border: none; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

def get_data():
    # استخدام فريم 15 دقيقة لبيانات الجلسات لسرعة التحميل ودقة المستويات
    df = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=True)
    if not df.empty:
        df.index = df.index.tz_convert(ny_tz)
    return df

def get_session_high_low(df, start_time, end_time):
    try:
        session_data = df.between_time(start_time, end_time)
        if not session_data.empty:
            return session_data['High'].max(), session_data['Low'].min()
    except:
        pass
    return 0.0, 0.0

def get_sb_status(current_ny):
    windows = [("03:00", "04:00", "L"), ("10:00", "11:00", "NY am"), ("14:00", "15:00", "NY pm")]
    for start_str, end_str, label in windows:
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()
        start_dt = datetime.combine(current_ny.date(), start).replace(tzinfo=ny_tz)
        end_dt = datetime.combine(current_ny.date(), end).replace(tzinfo=ny_tz)
        if start_dt <= current_ny <= end_dt: return f"🔥 ACTIVE: {label}", ""
        if current_ny < start_dt:
            diff = start_dt - current_ny
            return f"⏳ {label}", f"{int(diff.total_seconds() / 3600)}h {int((diff.total_seconds() % 3600) / 60)}m"
    next_london = datetime.combine(current_ny.date() + timedelta(days=1), datetime.strptime("03:00", "%H:%M").time()).replace(tzinfo=ny_tz)
    diff = next_london - current_ny
    return "⏳ L", f"{int(diff.total_seconds() / 3600)}h {int((diff.total_seconds() % 3600) / 60)}m"

# --- عنوان التطبيق ---
st.title("🏆 رادار الذهب - Silver Bullet Pro")
st.write("رصد السيولة (15m High/Low) والشموع اليابانية التفاعلية")

# --- منطقة العرض الرئيسية ---
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            df = get_data()
            if not df.empty:
                now_ny = datetime.now(ny_tz)
                now_bg = datetime.now(bg_tz)
                latest_close = df['Close'].iloc[-1].item()
                
                # 1. حساب Midnight Open (00:00 NY)
                m_data = df[df.index.date == now_ny.date()].between_time('00:00', '00:15')
                mn_open = m_data['Open'].iloc[0].item() if not m_data.empty else df['Open'].iloc[-1].item()
                
                # 2. حساب مستويات السيولة لجلسات اليوم
                asia_h, asia_l = get_session_high_low(df, "20:00", "00:00")
                london_h, london_l = get_session_high_low(df, "02:00", "05:00")
                
                # 3. إشارة الاتجاه (فوق/تحت Midnight Open)
                if latest_close < mn_open:
                    direction_text = f"📈 Direction: BUY (Price below {mn_open:.2f}) 🟢"
                    direction_color = "success"
                else:
                    direction_text = f"📉 Direction: SELL (Price above {mn_open:.2f}) 🔴"
                    direction_color = "error"

                # --- العرض في الصفحة (المربعات) ---
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🇮🇶 Baghdad", now_bg.strftime("%H:%M"))
                col2.metric("🇺🇸 New York", now_ny.strftime("%H:%M"))
                col3.metric("💰 Gold Price", f"{latest_close:.2f}")
                col4.metric("🎯 Midnight Open", f"{mn_open:.2f}")
                
                st.divider()
                
                # العداد وحالة السيولة
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                sb_label, sb_time = get_sb_status(now_ny)
                col_c1.metric(f"⏰ Next: {sb_label}", sb_time if sb_time else "Now!")
                col_c2.metric("🇬🇧 London High", f"{london_h:.2f}" if london_h > 0 else "Pending")
                col_c3.metric("🇬🇧 London Low", f"{london_l:.2f}" if london_l > 0 else "Pending")
                col_c4.metric("🌏 Asia High", f"{asia_h:.2f}" if asia_h > 0 else "Pending")

                # إظهار الاتجاه (فوق/تحت Midnight Open)
                if direction_color == "success": st.success(direction_text)
                else: st.error(direction_text)

                # --- إنشاء شارت الشموع اليابانية (Plotly) ---
                st.markdown("### 📊 Interactive Candlestick Chart (15m)")
                fig = go.Figure(data=[go.Candlestick(x=df.index,
                                                      open=df['Open'],
                                                      high=df['High'],
                                                      low=df['Low'],
                                                      close=df['Close'],
                                                      name='Gold 15m',
                                                      increasing_line_color='#00ff00', # شموع خضراء
                                                      decreasing_line_color='#ff0000')]) # شموع حمراء
                
                # أ) رسم خط Midnight Open (أبيض متقطع)
                fig.add_hline(y=mn_open, line_dash="dash", line_color="#ffffff", line_width=1.5, annotation_text=f"Midnight Open: {mn_open:.2f}", annotation_position="top right")
                
                # ب) رسم مستويات آسيا (أزرق متصل)
                if asia_h > 0: fig.add_hline(y=asia_h, line_color="#3498db", line_width=1.5, annotation_text=f"Asia High: {asia_h:.2f}", annotation_position="bottom right")
                if asia_l > 0: fig.add_hline(y=asia_l, line_color="#3498db", line_width=1.5, annotation_text=f"Asia Low: {asia_l:.2f}", annotation_position="top right")
                
                # ج) رسم مستويات لندن (أصفر متصل)
                if london_h > 0: fig.add_hline(y=london_h, line_color="#f1c40f", line_width=1.5, annotation_text=f"London High: {london_h:.2f}", annotation_position="bottom right")
                if london_l > 0: fig.add_hline(y=london_l, line_color="#f1c40f", line_width=1.5, annotation_text=f"London Low: {london_l:.2f}", annotation_position="top right")

                # إعدادات مظهر الشارت
                fig.update_layout(template="plotly_dark",
                                   xaxis_title="NY Time",
                                   yaxis_title="Price",
                                   xaxis_rangeslider_visible=False,
                                   height=600,
                                   margin=dict(l=20, r=20, t=20, b=20),
                                   paper_bgcolor="#1e2130",
                                   plot_bgcolor="#1e2130")
                
                # عرض الشارت التفاعلي
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
        except Exception as e:
            st.warning(f"Updating data... (15m Frame)")
            
    time.sleep(60)
    st.rerun()
