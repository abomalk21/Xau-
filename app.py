import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- الإعدادات الأساسية ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.set_page_config(page_title="XAU LIVE", layout="wide")

@st.cache_data(ttl=10)
def get_data():
    try:
        # جلب الذهب المباشر
        df = yf.download("GC=F", period="1d", interval="5m", progress=False) # فريم 5 د لتفاصيل أكثر
        if df.empty: return None
        df.index = df.index.tz_convert(ny_tz)
        return df.dropna()
    except: return None

st.title("🏆 XAU")
data = get_data()

if data is not None:
    now_ny = datetime.now(ny_tz)
    last_p = float(data['Close'].iloc[-1])
    
    # العدادات العلوية
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold Live", f"{last_p:.2f}")
    
    # حساب Midnight
    mn_val = float(data.iloc[0]['Open']) # أول سعر في اليوم
    c2.metric("🎯 Midnight", f"{mn_val:.2f}")
    
    # عداد الشمعة (5 دقائق)
    rem_s = (5 - (now_ny.minute % 5)) * 60 - now_ny.second
    c3.metric("⏳ Bar Ends", f"{rem_s//60:02d}:{rem_s%60:02d}")
    
    # السلفر بوليت
    sb = next((now_ny.replace(hour=h, minute=0, second=0) for h in [10, 14]| if now_ny.replace(hour=h, minute=0, second=0) > now_ny), now_ny + timedelta(hours=1))
    diff = sb - now_ny
    c4.metric("🏹 Next SB", f"{diff.seconds//3600:02d}h {(diff.seconds//60)%60:02d}m")

    # --- حل مشكلة اختفاء الشموع الجذري ---
    # نأخذ آخر 30 شمعة فقط لضمان حجم ضخم
    df_plot = data.tail(30)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_plot.index,
        open=df_plot['Open'], high=df_plot['High'],
        low=df_plot['Low'], close=df_plot['Close']
    )])

    # إضافة خط Midnight
    fig.add_hline(y=mn_val, line_color="red", line_width=2, annotation_text="MIDNIGHT")

    # إعدادات المحور "الانتحارية" (تفرض نفسها على التابلت)
    fig.update_layout(
        template="plotly_dark",
        height=600,
        margin=dict(l=0, r=50, t=0, b=0),
        xaxis_rangeslider_visible=False,
        yaxis=dict(
            side="right",
            autorange=True, # أهم خيار
            fixedrange=False, # يسمح لك بالتحريك يدوياً
            range=[last_p - 10, last_p + 10] # إجبار المحور على السعر الحالي
        ),
        # منع الشارت من حفظ الزووم القديم
        uirevision='constant' 
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # شريط التوقيت السفلي
    st.markdown("---")
    st.write(f"🇮🇶 Baghdad: `{datetime.now(bg_tz).strftime('%H:%M')}` | 🇺🇸 NY: `{now_ny.strftime('%H:%M')}`")
    if st.button('🚀 Reset Chart View'): st.rerun()

else:
    st.error("Connection Lost. Refreshing...")
    st.rerun()
