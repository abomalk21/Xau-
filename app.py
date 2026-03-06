import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات الواجهة ---
st.set_page_config(page_title="XAU", layout="wide")
ny_tz = pytz.timezone('America/New_York')

@st.cache_data(ttl=60)
def get_xau_data():
    try:
        data = yf.download("GC=F DX-Y", period="2d", interval="15m", progress=False, auto_adjust=True)
        if data.empty: return None, None
        gold = data.xs('GC=F', axis=1, level=1)
        dxy = data.xs('DX-Y', axis=1, level=1)
        gold.index = gold.index.tz_convert(ny_tz)
        return gold, dxy
    except: return None, None

st.title("🏆 XAU")
g_df, d_df = get_xau_data()

if g_df is not None and len(g_df) > 2:
    latest_g = float(g_df['Close'].iloc[-1])
    now_ny = datetime.now(ny_tz)
    
    # 1. حساب Midnight Open
    mid_df = g_df[g_df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(g_df['Open'].iloc[0])

    # 2. حساب مستويات الجلسات
    asia = g_df.between_time("20:00", "00:00")
    london = g_df.between_time("02:00", "05:00")
    ah, al = (asia['High'].max(), asia['Low'].min()) if not asia.empty else (0, 0)
    lh, ll = (london['High'].max(), london['Low'].min()) if not london.empty else (0, 0)

    # المربعات العلوية
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{mn_open:.2f}")
    c3.metric("🇺🇸 NY Time", now_ny.strftime("%H:%M"))

    # الشارت المطور (عرض 120 شمعة لرؤية أشمل)
    plot_df = g_df.tail(120) 
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], 
        high=plot_df['High'], low=plot_df['Low'], 
        close=plot_df['Close'], name="XAU")])

    # --- جعل الخطوط أكثر ظهراً (زيادة السماكة line_width) ---
    # خط منتصف الليل (أحمر عريض)
    fig.add_hline(y=mn_open, line_color="red", line_width=3, annotation_text="MIDNIGHT", annotation_font_size=15)
    
    # خطوط آسيا (أزرق سماوي عريض جداً ومتصل للوضوح)
    if ah > 0:
        fig.add_hline(y=ah, line_color="#00FFFF", line_width=3, line_dash="solid", annotation_text="ASIA HIGH", annotation_font_color="#00FFFF")
        fig.add_hline(y=al, line_color="#00FFFF", line_width=3, line_dash="solid", annotation_text="ASIA LOW", annotation_font_color="#00FFFF")
    
    # خطوط لندن (أصفر منقط عريض)
    if lh > 0:
        fig.add_hline(y=lh, line_color="yellow", line_width=2, line_dash="dot", annotation_text="LONDON H")
        fig.add_hline(y=ll, line_color="yellow", line_width=2, line_dash="dot", annotation_text="LONDON L")

    fig.update_layout(
        template="plotly_dark", height=700, margin=dict(l=0,r=0,t=0,b=0),
        xaxis_rangeslider_visible=False,
        # تحسين شريط الأدوات ليظهر بوضوح أكبر على التابلت
        modebar=dict(bgcolor='rgba(0,0,0,0)', color='white', activecolor='yellow')
    )
    
    # تكبير أزرار التحكم وتحسين استجابة اللمس
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True, 
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraselayer'], # إضافة أدوات رسم يدوية
        'toImageButtonOptions': {'format': 'png', 'scale': 2} # لجعل زر الكاميرا يحفظ صورة بجودة عالية
    })

    st.write(f"🌏 **Asia Range:** {al:.2f} - {ah:.2f} | 🇬🇧 **London Range:** {ll:.2f} - {lh:.2f}")

else:
    st.info("جاري التحديث...")

if st.button('🔄 Update Now'): st.rerun()
