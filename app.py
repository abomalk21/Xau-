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
        # جلب بيانات يومين لضمان ظهور الجلسات السابقة
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
    
    # 1. حساب Midnight Open بدقة
    mid_df = g_df[g_df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(g_df['Open'].iloc[0])

    # 2. حساب مستويات الجلسات السابقة
    asia = g_df.between_time("20:00", "00:00").tail(16)
    london = g_df.between_time("02:00", "05:00").tail(12)
    ah, al = (asia['High'].max(), asia['Low'].min()) if not asia.empty else (0, 0)
    lh, ll = (london['High'].max(), london['Low'].min()) if not london.empty else (0, 0)

    # عرض العدادات العلوية
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{mn_open:.2f}")
    c3.metric("🇺🇸 NY Time", now_ny.strftime("%H:%M"))

    # تحليل Judas Swing والتحذيرات النصية
    st.markdown("### 🛡️ Smart Monitor")
    checks = []
    g_change = g_df['Close'].iloc[-1] - g_df['Close'].iloc[-4]
    d_change = d_df['Close'].iloc[-1] - d_df['Close'].iloc[-4]
    if g_change > 0 and d_change > 0: checks.append("⚠️ SMT: الذهب والدولار يصعدان معاً")
    
    if lh > 0 and latest_g > lh and latest_g > mn_open:
        checks.append("🔍 Judas Swing: سحب سيولة قمة لندن فوق خط MN (توقع هبوط)")
    elif ll > 0 and latest_g < ll and latest_g < mn_open:
        checks.append("🔍 Judas Swing: سحب سيولة قاع لندن تحت خط MN (توقع صعود)")

    if checks:
        for c in checks: st.warning(c)
    else: st.info("✅ الهيكل متناغم حالياً")

    # رسم الشارت مع تعديل خط منتصف الليل
    fig = go.Figure(data=[go.Candlestick(
        x=g_df.index[-50:], open=g_df['Open'][-50:], 
        high=g_df['High'][-50:], low=g_df['Low'][-50:], 
        close=g_df['Close'][-50:], name="XAU")])

    # --- تعديل خط منتصف الليل ليصبح أحمر متصل ---
    fig.add_hline(y=mn_open, line_color="red", line_width=2, annotation_text="Midnight Open", annotation_font_color="red")
    
    # خطوط لندن (صفراء)
    if lh > 0: fig.add_hline(y=lh, line_color="yellow", line_dash="dot", line_width=1, annotation_text="London H")
    if ll > 0: fig.add_hline(y=ll, line_color="yellow", line_dash="dot", line_width=1, annotation_text="London L")
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.write(f"🌏 Asia: H {ah:.2f} | L {al:.2f}  ---  🇬🇧 London: H {lh:.2f} | L {ll:.2f}")

else:
    st.info("جاري تحديث البيانات...")

if st.button('🔄 Update'): st.rerun()
