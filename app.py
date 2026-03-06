import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات الوقت الأساسية ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.set_page_config(page_title="XAU", layout="wide")

@st.cache_data(ttl=15) # تحديث سريع جداً
def get_xau():
    try:
        # استخدام الرمز المباشر للذهب الفوري لضمان البيانات
        df = yf.download("GC=F", period="2d", interval="15m", progress=False)
        if df.empty: return None
        df.index = df.index.tz_convert(ny_tz)
        return df.dropna()
    except: return None

st.title("🏆 XAU")
data = get_xau()

if data is not None and not data.empty:
    now_ny = datetime.now(ny_tz)
    
    # 1. المربعات العلوية
    last_price = float(data['Close'].iloc[-1])
    mn_price = float(data.between_time('00:00', '00:15')['Open'].iloc[0]) if not data.between_time('00:00', '00:15').empty else float(data['Open'].iloc[0])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{last_price:.2f}")
    c2.metric("🎯 Midnight", f"{mn_price:.2f}")
    c3.metric("⏳ Bar Ends", f"{14 - (now_ny.minute % 15):02d}:{59 - now_ny.second:02d}")
    
    sb_target = next((now_ny.replace(hour=h, minute=0, second=0) for h in [3, 10, 14] if now_ny.replace(hour=h, minute=0, second=0) > now_ny), now_ny.replace(hour=3, minute=0, second=0) + timedelta(days=1))
    c4.metric("🏹 Next SB", f"{(sb_target - now_ny).seconds // 3600:02d}h {((sb_target - now_ny).seconds // 60) % 60:02d}m")

    # 2. الشارت (إجبار المحور Y على السعر الحالي)
    plot_df = data.tail(80) # تقليل عدد الشموع لزيادة الوضوح
    
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index,
        open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    )])

    # إضافة خطوط الجلسات (أصفر منقط)
    for s, e, n in [("20:00", "00:00", "ASIA"), ("02:00", "05:00", "LONDON")]:
        sess = data.between_time(s, e)
        if not sess.empty:
            fig.add_hline(y=float(sess['High'].max()), line_color="yellow", line_dash="dot", annotation_text=f"{n} H")
            fig.add_hline(y=float(sess['Low'].min()), line_color="yellow", line_dash="dot", annotation_text=f"{n} L")

    fig.add_hline(y=mn_price, line_color="red", line_width=2, annotation_text="MIDNIGHT")

    # إعدادات إظهار الشموع الإجباري
    fig.update_layout(
        template="plotly_dark", height=700, margin=dict(l=0,r=50,t=0,b=0),
        xaxis_rangeslider_visible=False,
        yaxis=dict(
            autorange=True, # جعل المحور يتحرك مع السعر تلقائياً
            fixedrange=False,
            side="right",
            gridcolor="#333333"
        )
    )

    # تفعيل أزرار التحكم بالكامل
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True})

    # 3. شريط الأخبار والمواقيت بالأسفل تماماً
    st.markdown("---")
    st.error("🚨 **Friday High Volatility Alert:** NFP/Jobs Report at 08:30 AM NY Time.")
    st.markdown(f"🕒 **Baghdad:** `{datetime.now(bg_tz).strftime('%H:%M')}` | 🇺🇸 **New York:** `{now_ny.strftime('%H:%M')}`")

else:
    st.warning("⚠️ لا توجد بيانات حالياً. يرجى الضغط على الزر أدناه لتنشيط الاتصال.")
    if st.button('🚀 Force Reset Connection'): st.rerun()
