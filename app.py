import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات سريعة ومستقرة ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')
ldn_tz = pytz.timezone('Europe/London')

st.set_page_config(page_title="XAU", layout="wide")

@st.cache_data(ttl=30)
def get_gold_data():
    try:
        # جلب بيانات الذهب فقط لضمان السرعة القصوى
        g = yf.download("GC=F", period="2d", interval="15m", progress=False)
        if g.empty: return None
        g.index = g.index.tz_convert(ny_tz)
        return g
    except: return None

st.title("🏆 XAU") 
g_df = get_gold_data()

if g_df is not None and not g_df.empty:
    now_ny = datetime.now(ny_tz)
    now_bg = datetime.now(bg_tz)
    now_ldn = datetime.now(ldn_tz)
    
    # 1. المربعات العلوية
    latest_price = float(g_df['Close'].iloc[-1])
    mn_df = g_df.between_time('00:00', '00:15')
    mn_price = float(mn_df['Open'].iloc[0]) if not mn_df.empty else float(g_df['Open'].iloc[0])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{latest_price:.2f}")
    c2.metric("🎯 Midnight", f"{mn_price:.2f}")
    c3.metric("⏳ Bar Ends", f"{14 - (now_ny.minute % 15):02d}:{59 - now_ny.second:02d}")
    
    sb_target = next((now_ny.replace(hour=h, minute=0, second=0) for h in [3, 10, 14] if now_ny.replace(hour=h, minute=0, second=0) > now_ny), now_ny.replace(hour=3, minute=0, second=0) + timedelta(days=1))
    sb_diff = sb_target - now_ny
    c4.metric("🏹 Next SB", f"{sb_diff.seconds // 3600:02d}h {(sb_diff.seconds // 60) % 60:02d}m")

    # 2. الشارت (إصلاح ظهور الشموع وأدوات التحكم)
    plot_df = g_df.tail(100)
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index,
        open=plot_df['Open'],
        high=plot_df['High'],
        low=plot_df['Low'],
        close=plot_df['Close'],
        name="XAU"
    )])
    
    # توحيد مستويات آسيا ولندن (أصفر منقط)
    for s_start, s_end, s_name in [("20:00", "00:00", "ASIA"), ("02:00", "05:00", "LONDON")]:
        sess = g_df.between_time(s_start, s_end)
        if not sess.empty:
            fig.add_hline(y=float(sess['High'].max()), line_color="yellow", line_dash="dot", annotation_text=f"{s_name} H")
            fig.add_hline(y=float(sess['Low'].min()), line_color="yellow", line_dash="dot", annotation_text=f"{s_name} L")
    
    fig.add_hline(y=mn_price, line_color="red", line_width=2, annotation_text="MIDNIGHT")
    
    # تفعيل شريط التحكم (displayModeBar=True) وإصلاح المحاور لظهور الشموع
    fig.update_layout(
        template="plotly_dark", 
        height=750, 
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        yaxis=dict(autorange=True, fixedrange=False) # لضمان ظهور الشموع وعدم اختفائها
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True})

    # 3. شريط الأخبار والمواقيت بالأسفل
    st.markdown("---")
    st.info(f"📅 **Friday Alert:** High Volatility. Watch for NFP/Jobs Report (08:30 AM NY Time).")
    st.markdown(f"""
    🕒 **Time Engine:** 🇮🇶 Baghdad: `{now_bg.strftime('%H:%M')}` | 🇬🇧 London: `{now_ldn.strftime('%H:%M')}` | 🇺🇸 NY: `{now_ny.strftime('%H:%M')}`
    """)

else:
    st.info("🔄 Syncing Data...")

if st.button('🔄 Refresh'): st.rerun()
