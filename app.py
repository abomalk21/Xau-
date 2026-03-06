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

st.set_page_config(page_title="XAU", layout="wide")

@st.cache_data(ttl=20) # تحديث أسرع للسعر اللحظي
def get_xau_data():
    try:
        # استخدام الرمز المباشر لضمان مطابقة المنصة
        data = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=True)
        if data.empty: return None
        data.index = data.index.tz_convert(ny_tz)
        return data
    except: return None

st.title("🏆 XAU")
g_df = get_xau_data()

if g_df is not None and len(g_df) > 2:
    # التأكد من تحويل السعر إلى رقم بسيط لتجنب الأخطاء
    latest_g = float(g_df['Close'].iloc[-1])
    now_ny = datetime.now(ny_tz)
    now_bg = datetime.now(bg_tz)
    now_ldn = datetime.now(ldn_tz)
    
    # العدادات العلوية (قاعدتك الأساسية)
    rem_min = 14 - (now_ny.minute % 15)
    rem_sec = 59 - now_ny.second
    
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

    # حساب المستويات - مع إضافة .item() لتجنب خطأ ValueError
    mid_df = g_df[g_df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(g_df['Open'].iloc[0])
    
    asia = g_df.between_time("20:00", "00:00")
    ah = float(asia['High'].max()) if not asia.empty else 0.0
    al = float(asia['Low'].min()) if not asia.empty else 0.0
    
    london = g_df.between_time("02:00", "05:00")
    lh = float(london['High'].max()) if not london.empty else 0.0
    ll = float(london['Low'].min()) if not london.empty else 0.0

    # عرض البيانات
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold Live", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{mn_open:.2f}")
    c3.metric("⏳ Bar Ends", f"{rem_min:02d}:{rem_sec:02d}")
    c4.metric("🏹 Next SB", f"{sb_h:02d}h {sb_m:02d}m")

    # الشارت
    plot_df = g_df.tail(120) 
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="XAU")])

    fig.add_hline(y=mn_open, line_color="red", line_width=3, annotation_text="MIDNIGHT")
    
    # توحيد التنسيق (أصفر منقط)
    if ah > 0:
        fig.add_hline(y=ah, line_color="yellow", line_dash="dot", annotation_text="ASIA H")
        fig.add_hline(y=al, line_color="yellow", line_dash="dot", annotation_text="ASIA L")
    if lh > 0:
        fig.add_hline(y=lh, line_color="yellow", line_dash="dot", annotation_text="LONDON H")
        fig.add_hline(y=ll, line_color="yellow", line_dash="dot", annotation_text="LONDON L")

    fig.update_layout(template="plotly_dark", height=750, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

    # الإضافات السفلية
    st.markdown("---")
    st.markdown(f"🕒 **Baghdad:** `{now_bg.strftime('%H:%M')}` | 🇺🇸 **NY:** `{now_ny.strftime('%H:%M')}`")
    st.warning("⚠️ **Friday Alert:** High Volatility Session.")

else:
    st.info("جاري تحديث السعر اللحظي...")

if st.button('🔄 Force Update'): st.rerun()
