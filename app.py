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
def get_clean_data():
    try:
        # جلب البيانات بشكل منفصل لضمان أعلى سرعة واستقرار
        g = yf.download("GC=F", period="2d", interval="15m", progress=False)
        d = yf.download("DX-Y", period="2d", interval="15m", progress=False)
        if g.empty or d.empty: return None, None
        g.index = g.index.tz_convert(ny_tz)
        return g, d
    except: return None, None

st.title("🏆 XAU") # الاسم الأصلي دون تغيير
g_df, d_df = get_clean_data()

if g_df is not None and not g_df.empty:
    now_ny = datetime.now(ny_tz)
    now_bg = datetime.now(bg_tz)
    now_ldn = datetime.now(ldn_tz)
    
    # 1. تنبيه الأخبار البصري (Friday Focus)
    st.warning("⚠️ **Friday Alert:** High Volatility Session. Monitor NFP/Jobs Data at 08:30 AM NY Time.")

    # 2. المربعات العلوية
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{g_df['Close'].iloc[-1]:.2f}")
    
    mn_df = g_df.between_time('00:00', '00:15')
    mn_price = mn_df['Open'].iloc[0] if not mn_df.empty else g_df['Open'].iloc[0]
    c2.metric("🎯 Midnight", f"{mn_price:.2f}")
    
    # عداد الشمعة 15 دقيقة
    c3.metric("⏳ Bar Ends", f"{14 - (now_ny.minute % 15):02d}:{59 - now_ny.second:02d}")
    
    # عداد السلفر بوليت
    sb_target = next((now_ny.replace(hour=h, minute=0, second=0) for h in [3, 10, 14] if now_ny.replace(hour=h, minute=0, second=0) > now_ny), now_ny.replace(hour=3, minute=0, second=0) + timedelta(days=1))
    sb_diff = sb_target - now_ny
    c4.metric("🏹 Next SB", f"{sb_diff.seconds // 3600:02d}h {(sb_diff.seconds // 60) % 60:02d}m")

    # 3. الشارت (100 شمعة فريم 15 دقيقة)
    fig = go.Figure(data=[go.Candlestick(x=g_df.tail(100).index, open=g_df.tail(100)['Open'], high=g_df.tail(100)['High'], low=g_df.tail(100)['Low'], close=g_df.tail(100)['Close'])])
    
    # توحيد تنسيق خطوط آسيا ولندن (أصفر منقط)
    for s_start, s_end, s_name in [("20:00", "00:00", "ASIA"), ("02:00", "05:00", "LONDON")]:
        sess = g_df.between_time(s_start, s_end)
        if not sess.empty:
            fig.add_hline(y=sess['High'].max(), line_color="yellow", line_dash="dot", annotation_text=f"{s_name} H")
            fig.add_hline(y=sess['Low'].min(), line_color="yellow", line_dash="dot", annotation_text=f"{s_name} L")
    
    fig.add_hline(y=mn_price, line_color="red", line_width=2, annotation_text="MIDNIGHT")
    fig.update_layout(template="plotly_dark", height=700, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 4. السطر السفلي (DXY والمواقيت)
    st.markdown("---")
    st.markdown(f"""
    📈 **DXY Index:** `{d_df['Close'].iloc[-1]:.3f}` | 
    🇮🇶 **Baghdad:** `{now_bg.strftime('%H:%M')}` | 
    🇬🇧 **London:** `{now_ldn.strftime('%H:%M')}` | 
    🇺🇸 **NY:** `{now_ny.strftime('%H:%M')}`
    """)

else:
    st.info("🔄 Syncing Market Data...")

if st.button('🔄 Refresh Data'): st.rerun()
