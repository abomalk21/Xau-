import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go

# --- إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="Gold Tracker Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 35px !important; color: #f1c40f !important; font-weight: bold; }
    .stAlert { border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

# --- جلب البيانات (تخزين مؤقت لضمان السرعة) ---
@st.cache_data(ttl=60)
def get_data():
    try:
        # نطلب بيانات يوم واحد بفريم 15 دقيقة (الأسرع والأدق للسيولة)
        df = yf.download("GC=F", period="1d", interval="15m", progress=False, auto_adjust=True)
        if not df.empty:
            df.index = df.index.tz_convert(ny_tz)
            return df
    except:
        return pd.DataFrame()
    return pd.DataFrame()

# --- حساب المستويات ---
def calculate_metrics(df):
    if df is None or df.empty: return None
    try:
        now_ny = datetime.now(ny_tz)
        
        # 1. Midnight Open
        midnight_df = df[df.index.date == now_ny.date()].between_time('00:00', '00:15')
        mn_open = midnight_df['Open'].iloc[0] if not midnight_df.empty else df['Open'].iloc[0]
        
        # 2. Session High/Low
        asia = df.between_time("20:00", "00:00")
        london = df.between_time("02:00", "05:00")
        
        return {
            "latest": float(df['Close'].iloc[-1]),
            "mn_open": float(mn_open),
            "asia_h": float(asia['High'].max()) if not asia.empty else 0.0,
            "asia_l": float(asia['Low'].min()) if not asia.empty else 0.0,
            "london_h": float(london['High'].max()) if not london.empty else 0.0,
            "london_l": float(london['Low'].min()) if not london.empty else 0.0,
            "df_plot": df.tail(40)
        }
    except:
        return None

# --- نظام العداد ---
def get_timer(now_ny):
    windows = [("03:00", "L"), ("10:00", "NY am"), ("14:00", "NY pm")]
    for start_str, label in windows:
        start_dt = datetime.combine(now_ny.date(), datetime.strptime(start_str, "%H:%M").time()).replace(tzinfo=ny_tz)
        if now_ny < start_dt:
            diff = start_dt - now_ny
            hours, rem = divmod(int(diff.total_seconds()), 3600)
            mins = rem // 60
            return f"{label}", f"{hours}h {mins}m"
    return "L (Tomorrow)", "--:--"

# --- العرض الرئيسي ---
st.title("🏆 رادار الذهب - Silver Bullet Pro")
container = st.empty()

while True:
    with container.container():
        raw_df = get_data()
        m = calculate_metrics(raw_df)
        
        # تأكد من أن البيانات موجودة قبل محاولة عرضها (حل مشكلة TypeError)
        if m is not None:
            now_ny = datetime.now(ny_tz)
            now_bg = datetime.now(bg_tz)
            
            # عرض المربعات العلوية
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Gold Now", f"{m['latest']:.2f}")
            c2.metric("🎯 Midnight", f"{m['mn_open']:.2f}")
            c3.metric("🇮🇶 Baghdad", now_bg.strftime("%H:%M"))
            c4.metric("🇺🇸 NY Time", now_ny.strftime("%H:%M"))
            
            # إشارة الاتجاه
            if m['latest'] < m['mn_open']:
                st.success(f"🟢 BUY ZONE | Price Below Midnight | ▲")
            else:
                st.error(f"🔴 SELL ZONE | Price Above Midnight | ▼")
            
            # الشارت التفاعلي (الشموع اليابانية)
            fig = go.Figure(data=[go.Candlestick(
                x=m['df_plot'].index,
                open=m['df_plot']['Open'], high=m['df_plot']['High'],
                low=m['df_plot']['Low'], close=m['df_plot']['Close'],
                name="Gold"
            )])
            
            # إضافة خط منتصف الليل والسيولة
            fig.add_hline(y=m['mn_open'], line_dash="dash", line_color="white", annotation_text="Midnight")
            if m['london_h'] > 0: fig.add_hline(y=m['london_h'], line_color="#f1c40f", line_width=1, annotation_text="London High")
            if m['asia_h'] > 0: fig.add_hline(y=m['asia_h'], line_color="#3498db", line_width=1, annotation_text="Asia High")

            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # البيانات الجانبية
            st.divider()
            b1, b2, b3 = st.columns(3)
            next_l, next_t = get_timer(now_ny)
            b1.metric(f"⏰ Next: {next_l}", next_t)
            b2.write(f"🇬🇧 **London:** H {m['london_h']:.2f} | L {m['london_l']:.2f}")
            b3.write(f"🌏 **Asia:** H {m['asia_h']:.2f} | L {m['asia_l']:.2f}")
        else:
            st.info("جاري تهيئة البيانات... انتظر لحظة")
            time.sleep(2)

    time.sleep(60)
    st.rerun()
