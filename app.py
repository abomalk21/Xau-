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
    
    # 1. عداد وقت الشمعة (15 دقيقة)
    next_bar = (now_ny + timedelta(minutes=15)).replace(minute=(now_ny.minute // 15 + 1) * 15 % 60, second=0, microsecond=0)
    rem_bar = next_bar - now_ny
    
    # 2. حساب موعد السلفر بوليت (Silver Bullet) القادم
    # المواعيد: 3:00-4:00 AM (لندن) | 10:00-11:00 AM (نيويورك صباحاً) | 2:00-3:00 PM (نيويورك مساءً)
    sb_windows = [3, 10, 14] # الساعات بتوقيت نيويورك
    next_sb = None
    for hour in sb_windows:
        candidate = now_ny.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate > now_ny:
            next_sb = candidate
            break
    if not next_sb: # إذا انتهت مواعيد اليوم، نأخذ أول موعد غداً
        next_sb = (now_ny + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
    
    rem_sb = next_sb - now_ny
    sb_h, sb_m = divmod(rem_sb.seconds // 60, 60)

    # حساب المستويات
    mid_df = g_df[g_df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(g_df['Open'].iloc[0])
    asia = g_df.between_time("20:00", "00:00")
    london = g_df.between_time("02:00", "05:00")
    ah, al = (asia['High'].max(), asia['Low'].min()) if not asia.empty else (0, 0)
    lh, ll = (london['High'].max(), london['Low'].min()) if not london.empty else (0, 0)

    # عرض المربعات العلوية (4 أعمدة)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    c2.metric("🎯 Midnight", f"{mn_open:.2f}")
    c3.metric("⏳ Bar Ends", f"{rem_bar.seconds // 60:02d}:{rem_bar.seconds % 60:02d}")
    c4.metric("🏹 Next SB", f"{sb_h:02d}h {sb_m:02d}m")

    # الشارت
    plot_df = g_df.tail(120) 
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], 
        high=plot_df['High'], low=plot_df['Low'], 
        close=plot_df['Close'], name="XAU")])

    # خط منتصف الليل (أحمر عريض)
    fig.add_hline(y=mn_open, line_color="red", line_width=3, annotation_text="MIDNIGHT")
    
    # خطوط آسيا ولندن (تصميم موحد: منقط)
    if ah > 0:
        fig.add_hline(y=ah, line_color="#00FFFF", line_width=2, line_dash="dot", annotation_text="ASIA H")
        fig.add_hline(y=al, line_color="#00FFFF", line_width=2, line_dash="dot", annotation_text="ASIA L")
    if lh > 0:
        fig.add_hline(y=lh, line_color="yellow", line_width=2, line_dash="dot", annotation_text="LONDON H")
        fig.add_hline(y=ll, line_color="yellow", line_width=2, line_dash="dot", annotation_text="LONDON L")

    # --- تكبير أزرار التحكم 1.5 مرة وجعلها سوداء متباعدة ---
    fig.update_layout(
        template="plotly_dark", height=750, margin=dict(l=0,r=0,t=0,b=0),
        xaxis_rangeslider_visible=False,
        modebar=dict(
            bgcolor='black',
            color='white',
            activecolor='#00FFFF',
            thickness=60 # زيادة السماكة لجعل الأزرار ضخمة للتابلت
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True, 
        'displayModeBar': True,
        'displaylogo': False,
        'doubleClick': 'reset+autosize',
        'modeBarButtonsToAdd': ['zoomIn2d', 'zoomOut2d', 'autoScale2d'],
        'responsive': True
    })

    st.write(f"🌏 **Asia:** {al:.2f}-{ah:.2f} | 🇬🇧 **London:** {ll:.2f}-{lh:.2f} | 🕰 **NY:** {now_ny.strftime('%H:%M')}")

else:
    st.info("جاري التحديث...")

if st.button('🔄 Update Now'): st.rerun()
