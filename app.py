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
        # جلب بيانات الذهب فقط لتقليل الوزن وسرعة التحميل
        g = yf.download("GC=F", period="2d", interval="15m", progress=False)
        if g.empty: return None
        g.index = g.index.tz_convert(ny_tz)
        return g
    except: return None

st.title("🏆 XAU") # الاسم الأصلي
g_df = get_clean_data()

if g_df is not None and not g_df.empty:
    now_ny = datetime.now(ny_tz)
    now_bg = datetime.now(bg_tz)
    now_ldn = datetime.now(ldn_tz)
    
    # 1. تنبيه الأخبار (بصري)
    st.warning("⚠️ **Friday Alert:** High Volatility. Watch for NFP/Jobs Report (08:30 AM NY).")

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

    # 3. الشارت (100 شمعة فقط لأداء أسرع)
