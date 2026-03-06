import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- الإعدادات الأساسية ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.set_page_config(page_title="XAU Live", layout="wide")

@st.cache_data(ttl=15)
def get_data():
    try:
        # جلب البيانات - فريم 15 دقيقة لثبات الشارت
        df = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=True)
        if df.empty: return None
        df.index = df.index.tz_convert(ny_tz)
        return df.dropna()
    except: return None

st.title("🏆 XAU")
data = get_data()

if data is not None and len(data) > 2:
    now_ny = datetime.now(ny_tz)
    last_p = float(data['Close'].iloc[-1])
    
    # العدادات العلوية
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold Live", f"{last_p:.2f}")
    
    # حساب Midnight
    mid_df = data[data.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_val = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(data['Open'].iloc[0])
    c2.metric("🎯 Midnight", f"{mn_val:.2f}")
    
    # عداد الشمعة
    rem_min = 14 - (now_ny.minute % 15)
    rem_sec = 59 - now_ny.second
    c3.metric("⏳ Bar Ends", f"{rem_min:02d}:{rem_sec:02d}")
    
    # إصلاح خطأ السلفر بوليت
    sb_hours = [3, 10, 14]
    next_sb = next((now_ny.replace(hour=h, minute=0, second=0, microsecond=0) for h in sb_hours if now_ny.replace(hour=h, minute=0, second=0) > now_ny), (now_ny + timedelta(days=1)).replace(hour=3, minute=0, second=0))
    diff = next_sb - now_ny
    c4.metric("🏹 Next SB", f"{diff.seconds//3600:02d}h {(diff.seconds//60)%60:02d}m")

    # --- حل مشكلة اختفاء الشموع ---
    df_plot = data.tail(40) # آخر 40 شمعة لرؤية واضحة
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_plot.index, open=df_plot['Open'], high=df_plot['High'],
        low=df_plot['Low'], close=df_plot['Close']
    )])

    # إضافة المستويات
    fig.add_hline(y=mn_val, line_color="red", line_width=2, annotation_text="MIDNIGHT")
    
    # إعدادات الرؤية الإجبارية لمنع التجميد
    fig.update_layout(
        template="plotly_dark", height=650, margin=dict(l=0, r=50, t=0, b=0),
        xaxis_rangeslider_visible=False,
        yaxis=dict(side="right", autorange=True, fixedrange=False),
        uirevision='constant' # يمنع إعادة ضبط الزووم عند التحديث
    )

    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    # شريط المعلومات السفلي
    st.markdown("---")
    st.write(f"🇮🇶 Baghdad: `{datetime.now(bg_tz).strftime('%H:%M')}` | 🇺🇸 NY: `{now_ny.strftime('%H:%M')}`")
    st.warning("⚠️ **Friday Alert:** High Volatility Session.")

else:
    st.info("جاري مزامنة البيانات...")

if st.button('🔄 Refresh Now'): st.rerun()
