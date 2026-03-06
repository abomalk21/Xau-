import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات المناطق الزمنية ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')
ldn_tz = pytz.timezone('Europe/London')

st.set_page_config(page_title="XAU PRO RADAR", layout="wide")

@st.cache_data(ttl=60)
def get_market_data():
    try:
        # جلب البيانات بشكل منفصل لضمان الاستقرار
        g_data = yf.download("GC=F", period="2d", interval="15m", progress=False)
        d_data = yf.download("DX-Y", period="2d", interval="15m", progress=False)
        
        if g_data.empty or d_data.empty: return None, None
        
        g_data.index = g_data.index.tz_convert(ny_tz)
        d_data.index = d_data.index.tz_convert(ny_tz)
        return g_data, d_data
    except: return None, None

st.title("🏆 XAU PRO RADAR")
g_df, d_df = get_market_data()

# التحقق من وجود بيانات قبل المعالجة لتجنب IndexError
if g_df is not None and d_df is not None and len(d_df) > 0:
    latest_g = float(g_df['Close'].iloc[-1])
    latest_d = float(d_df['Close'].iloc[-1])
    now_ny = datetime.now(ny_tz)
    
    # 1. تنبيهات الأخبار البصرية (تحدث آلياً بناءً على أيام الأسبوع)
    today_name = now_ny.strftime('%A')
    st.info(f"📅 Today is {today_name}. Check Economic Calendar for High Impact News (CPI/FOMC).")
    
    # 2. العدادات العلوية
    rem_min = 14 - (now_ny.minute % 15)
    rem_sec = 59 - now_ny.second
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{g_df.between_time('00:00','00:15')['Open'].iloc[0]:.2f}")
    c3.metric("⏳ Bar Ends", f"{rem_min:02d}:{rem_sec:02d}")
    c4.metric("🏹 Next SB", "Calculated Below") # سيتم تحديثه في النسخة القادمة

    # 3. شارت الذهب مع المستويات الموحدة
    plot_df = g_df.tail(120) 
    fig = go.Figure(data=[go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'])])
    
    # مستويات آسيا ولندن (أصفر منقط)
    asia = g_df.between_time("20:00", "00:00")
    london = g_df.between_time("02:00", "05:00")
    
    if not asia.empty:
        fig.add_hline(y=asia['High'].max(), line_color="yellow", line_dash="dot", annotation_text="ASIA H")
        fig.add_hline(y=asia['Low'].min(), line_color="yellow", line_dash="dot", annotation_text="ASIA L")
    if not london.empty:
        fig.add_hline(y=london['High'].max(), line_color="yellow", line_dash="dot", annotation_text="LONDON H")
        fig.add_hline(y=london['Low'].min(), line_color="yellow", line_dash="dot", annotation_text="LONDON L")

    fig.update_layout(template="plotly_dark", height=700, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})

    # --- سطر DXY السفلي ومعلومات التوقيت ---
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(f"📈 DXY Index: {latest_d:.3f}")
        st.write(f"🇮🇶 Baghdad: `{datetime.now(bg_tz).strftime('%H:%M')}`")
    with col_b:
        st.write(f"🇺🇸 New York: `{now_ny.strftime('%H:%M')}`")
        st.write(f"🇬🇧 London: `{datetime.now(ldn_tz).strftime('%H:%M')}`")

else:
    st.warning("⚠️ Waiting for Market Data... Please refresh in a few seconds.")

if st.button('🔄 Refresh Radar'): st.rerun()
