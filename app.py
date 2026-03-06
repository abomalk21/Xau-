import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go

# --- إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="Gold Tracker 24h", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 35px !important; color: #f1c40f !important; font-weight: bold; }
    .stAlert { border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

# --- جلب البيانات (يوم واحد فقط لسرعة البرق) ---
@st.cache_data(ttl=60)
def get_data():
    try:
        # طلب بيانات يوم واحد يضمن جلب جلسة آسيا ولندن والافتتاح الحالي بأقل حجم
        df = yf.download("GC=F", period="1d", interval="15m", progress=False, auto_adjust=True)
        if not df.empty:
            df.index = df.index.tz_convert(ny_tz)
            return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return pd.DataFrame()

# --- حساب المستويات وجلسات السيولة ---
def calculate_metrics(df):
    if df.empty: return None
    
    now_ny = datetime.now(ny_tz)
    
    # 1. Midnight Open (00:00 NY)
    midnight_df = df[df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = midnight_df['Open'].iloc[0] if not midnight_df.empty else df['Open'].iloc[0]
    
    # 2. جلسة آسيا (تأخذ من بيانات مساء أمس إذا لزم الأمر)
    # ملاحظة: برغم طلب 1d، ياهو يوفر بيانات الساعات المتأخرة من أمس أحياناً
    asia = df.between_time("20:00", "00:00")
    london = df.between_time("02:00", "05:00")
    
    return {
        "latest": df['Close'].iloc[-1],
        "mn_open": mn_open,
        "asia_h": asia['High'].max() if not asia.empty else 0,
        "asia_l": asia['Low'].min() if not asia.empty else 0,
        "london_h": london['High'].max() if not london.empty else 0,
        "london_l": london['Low'].min() if not london.empty else 0,
        "df_plot": df.tail(40) # آخر 40 شمعة فقط للشارت
    }

# --- نظام العداد التنازلي ---
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
st.title("🏆 رادار الذهب - نسخة السرعة القصوى")
container = st.empty()

while True:
    with container.container():
        df = get_data()
        metrics = calculate_metrics(df)
        
        if metrics:
            now_ny = datetime.now(ny_tz)
            now_bg = datetime.now(bg_tz)
            
            # الصف العلوي: السعر والوقت
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Gold Now", f"{metrics['latest']:.2f}")
            c2.metric("🎯 Midnight", f"{metrics['mn_open']:.2f}")
            c3.metric("🇮🇶 Baghdad", now_bg.strftime("%H:%M"))
            c4.metric("🇺🇸 New York", now_ny.strftime("%H:%M"))
            
            # إشارة الاتجاه (أسهم ملونة)
            if metrics['latest'] < metrics['mn_open']:
                st.success(f"🟢 BUY ZONE | السعر تحت الافتتاح | ▲")
            else:
                st.error(f"🔴 SELL ZONE | السعر فوق الافتتاح | ▼")
            
            # شارت الشموع اليابانية
            fig = go.Figure(data=[go.Candlestick(
                x=metrics['df_plot'].index,
                open=metrics['df_plot']['Open'],
                high=metrics['df_plot']['High'],
                low=metrics['df_plot']['Low'],
                close=metrics['df_plot']['Close'],
                name="XAUUSD"
            )])
            
            # رسم خط منتصف الليل التلقائي
            fig.add_hline(y=metrics['mn_open'], line_dash="dash", line_color="white", annotation_text="Midnight Open")
            
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # بيانات الجلسات والعداد
            st.divider()
            b1, b2, b3 = st.columns(3)
            
            next_label, next_time = get_timer(now_ny)
            b1.metric(f"⏰ Next SB: {next_label}", next_time)
            
            b2.write(f"🇬🇧 **London:** H {metrics['london_h']:.2f} | L {metrics['london_l']:.2f}")
            b3.write(f"🌏 **Asia:** H {metrics['asia_h']:.2f} | L {metrics['asia_l']:.2f}")

        else:
            st.warning("جاري جلب البيانات من السيرفر...")

    time.sleep(60) # تحديث كل دقيقة لضمان استقرار التابلت
    st.rerun()
