import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات الوقت والمناطق ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')
ldn_tz = pytz.timezone('Europe/London')

st.set_page_config(page_title="XAU PRO RADAR", layout="wide")

@st.cache_data(ttl=60)
def get_full_data():
    try:
        # جلب البيانات بشكل منفصل لضمان استقرار المصفوفات
        gold = yf.download("GC=F", period="2d", interval="15m", progress=False)
        dxy = yf.download("DX-Y", period="2d", interval="15m", progress=False)
        if gold.empty or dxy.empty: return None, None
        gold.index = gold.index.tz_convert(ny_tz)
        dxy.index = dxy.index.tz_convert(ny_tz)
        return gold, dxy
    except: return None, None

st.title("🏆 XAU PRO RADAR")
g_df, d_df = get_full_data()

# فحص البيانات لتجنب IndexError
if g_df is not None and d_df is not None and len(d_df) > 0:
    now_ny = datetime.now(ny_tz)
    latest_g = float(g_df['Close'].iloc[-1])
    latest_d = float(d_df['Close'].iloc[-1])

    # 1. نظام تنبيهات الأخبار (بصري)
    st.warning("⚠️ **Friday Alert:** High Volatility expected. Watch for NFP/Jobs report at 08:30 AM NY Time.")

    # 2. حساب العدادات العلوية
    rem_min = 14 - (now_ny.minute % 15)
    rem_sec = 59 - now_ny.second
    
    # حساب السلفر بوليت
    sb_windows = [3, 10, 14] 
    next_sb = None
    for h in sb_windows:
        target = now_ny.replace(hour=h, minute=0, second=0, microsecond=0)
        if target > now_ny:
            next_sb = target
            break
    if not next_sb:
        next_sb = (now_ny + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
    diff_sb = next_sb - now_ny
    sb_h, sb_m = divmod(diff_sb.seconds // 60, 60)

    # 3. عرض المربعات العلوية
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{g_df.between_time('00:00','00:15')['Open'].iloc[0]:.2f}")
    c3.metric("⏳ Bar Ends", f"{rem_min:02d}:{rem_sec:02d}")
    c4.metric("🏹 Next SB", f"{sb_h:02d}h {sb_m:02d}m")

    # 4. الشارت (آسيا ولندن أصفر منقط)
    plot_df = g_df.tail(120) 
    fig = go.Figure(data=[go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'])])
    
    # إضافة المستويات
    asia = g_df.between_time("20:00", "00:00")
    london = g_df.between_time("02:00", "05:00")
    
    for df, label in [(asia, "ASIA"), (london, "LONDON")]:
        if not df.empty:
            fig.add_hline(y=df['High'].max(), line_color="yellow", line_dash="dot", annotation_text=f"{label} H")
            fig.add_hline(y=df['Low'].min(), line_color="yellow", line_dash="dot", annotation_text=f"{label} L")

    fig.update_layout(template="plotly_dark", height=700, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # 5. سطر DXY السفلي ومعلومات بغداد
    st.markdown("---")
    inf1, inf2, inf3 = st.columns(3)
    inf1.subheader(f"📈 DXY: {latest_d:.3f}")
    inf2.write(f"🇮🇶 Baghdad: `{datetime.now(bg_tz).strftime('%H:%M')}`")
    inf3.write(f"🇬🇧 London: `{datetime.now(ldn_tz).strftime('%H:%M')}`")

else:
    st.info("🔄 Waiting for data sync... Please click 'Refresh Radar' below.")

if st.button('🔄 Refresh Radar'): st.rerun()
