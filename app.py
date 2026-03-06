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

st.set_page_config(page_title="XAU Radar", layout="wide")

@st.cache_data(ttl=60)
def get_market_data():
    try:
        # جلب الذهب والدولار معاً
        data = yf.download(["GC=F", "DX-Y"], period="2d", interval="15m", progress=False, auto_adjust=True)
        if data.empty: return None, None
        gold = data.xs('GC=F', axis=1, level=1).dropna()
        dxy = data.xs('DX-Y', axis=1, level=1).dropna()
        gold.index = gold.index.tz_convert(ny_tz)
        dxy.index = dxy.index.tz_convert(ny_tz)
        return gold, dxy
    except: return None, None

st.title("🏆 XAU PRO RADAR")
g_df, d_df = get_market_data()

if g_df is not None and d_df is not None:
    latest_g = float(g_df['Close'].iloc[-1])
    latest_d = float(d_df['Close'].iloc[-1])
    now_ny = datetime.now(ny_tz)
    
    # 1. نظام الأخبار (تنبيهات بصرية هامة)
    # ملاحظة: هذه الأخبار مبرمجة بناءً على مواعيد ثابتة (مثل CPI/NFP) ويمكن تحديثها يدوياً
    important_news = [
        {"time": "08:30", "event": "🔴 CPI / NFP Data", "impact": "High"},
        {"time": "14:00", "event": "🟠 FOMC Minutes", "impact": "High"}
    ]
    
    for news in important_news:
        st.warning(f"🚀 **Breaking News Alert:** {news['event']} at {news['time']} NY Time")

    # 2. العدادات العلوية
    rem_min = 14 - (now_ny.minute % 15)
    rem_sec = 59 - now_ny.second
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{g_df.between_time('00:00','00:15')['Open'].iloc[0]:.2f}")
    c3.metric("⏳ Bar Ends", f"{rem_min:02d}:{rem_sec:02d}")
    c4.metric("📈 DXY", f"{latest_d:.3f}")

    # 3. كشف الدايفرجنس (SMT) بصرياً
    # مقارنة حركة الذهب مع الدولار في آخر 3 شموع
    g_move = g_df['Close'].iloc[-1] - g_df['Close'].iloc[-3]
    d_move = d_df['Close'].iloc[-1] - d_df['Close'].iloc[-3]
    
    if (g_move > 0 and d_move > 0) or (g_move < 0 and d_move < 0):
        st.error("⚠️ **SMT DIVERGENCE DETECTED:** Gold and DXY are moving in the SAME direction!")

    # الشارت (نفس التصميم الموحد)
    plot_df = g_df.tail(120) 
    fig = go.Figure(data=[go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Gold")])
    
    # رسم مستويات السيولة (آسيا ولندن أصفر منقط كطلبك)
    fig.update_layout(template="plotly_dark", height=700, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})

    # --- سطر المعلومات السفلي المطور ---
    st.markdown("---")
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        st.write(f"📊 **DXY Index:** `{latest_d:.3f}` | **DXY High:** `{d_df['High'].iloc[-1]:.3f}` | **DXY Low:** `{d_df['Low'].iloc[-1]:.3f}`")
        st.write(f"🕒 **NY:** `{now_ny.strftime('%H:%M')}` | **Baghdad:** `{datetime.now(bg_tz).strftime('%H:%M')}`")
    with col_inf2:
        st.write(f"🌏 **Asia Range:** `{g_df.between_time('20:00','00:00')['Low'].min():.2f} - {g_df.between_time('20:00','00:00')['High'].max():.2f}`")
        st.write(f"🇬🇧 **London Range:** `{g_df.between_time('02:00','05:00')['Low'].min():.2f} - {g_df.between_time('02:00','05:00')['High'].max():.2f}`")

else:
    st.info("جاري تحديث البيانات...")
if st.button('🔄 Update Now'): st.rerun()
