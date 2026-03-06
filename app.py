import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات الوقت ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.set_page_config(page_title="XAU", layout="wide")

@st.cache_data(ttl=10) # تحديث فائق السرعة
def get_xau_data():
    try:
        # جلب البيانات
        data = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=True)
        if data.empty: return None
        data.index = data.index.tz_convert(ny_tz)
        return data.dropna()
    except: return None

st.title("🏆 XAU")
g_df = get_xau_data()

if g_df is not None and len(g_df) > 2:
    latest_g = float(g_df['Close'].iloc[-1])
    now_ny = datetime.now(ny_tz)
    now_bg = datetime.now(bg_tz)
    
    # العدادات العلوية (نفس قيمك)
    rem_min = 14 - (now_ny.minute % 15)
    rem_sec = 59 - now_ny.second
    sb_windows = [3, 10, 14] 
    next_sb = next((now_ny.replace(hour=h, minute=0, second=0) for h in sb_windows if now_ny.replace(hour=h, minute=0, second=0) > now_ny), (now_ny + timedelta(days=1)).replace(hour=3, minute=0, second=0))
    diff_sb = next_sb - now_ny
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold Live", f"{latest_g:.2f}")
    
    # حساب المستويات رقمياً لضمان عدم حدوث ValueError
    mid_df = g_df[g_df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(g_df['Open'].iloc[0])
    c2.metric("🎯 Midnight", f"{mn_open:.2f}")
    c3.metric("⏳ Bar Ends", f"{rem_min:02d}:{rem_sec:02d}")
    c4.metric("🏹 Next SB", f"{diff_sb.seconds // 3600:02d}h {(diff_sb.seconds // 60) % 60:02d}m")

    # التركيز على آخر 40 شمعة فقط لضمان حجم ضخم للشموع
    plot_df = g_df.tail(40) 
    
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'],
        increasing_line_color='#00ff88', decreasing_line_color='#ff4444'
    )])

    # إضافة المستويات
    fig.add_hline(y=mn_open, line_color="red", line_width=2, annotation_text="MIDNIGHT")
    
    # جلسات آسيا ولندن
    for s, e, n in [("20:00", "00:00", "ASIA"), ("02:00", "05:00", "LONDON")]:
        sess = g_df.between_time(s, e)
        if not sess.empty:
            fig.add_hline(y=float(sess['High'].max()), line_color="yellow", line_dash="dot", annotation_text=f"{n} H")
            fig.add_hline(y=float(sess['Low'].min()), line_color="yellow", line_dash="dot", annotation_text=f"{n} L")

    # الإعدادات الإجبارية للرؤية
    fig.update_layout(
        template="plotly_dark", height=650, margin=dict(l=0,r=50,t=0,b=0),
        xaxis_rangeslider_visible=False,
        yaxis=dict(
            autorange=True, # توسيع تلقائي للمحور السعري
            fixedrange=False,
            side="right",
            gridcolor="#222"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    # شريط المعلومات السفلي
    st.markdown("---")
    st.markdown(f"🕒 **Baghdad:** `{now_bg.strftime('%H:%M')}` | 🇺🇸 **NY:** `{now_ny.strftime('%H:%M')}`")
    st.warning("⚠️ **Friday Alert:** High Volatility Session.")

else:
    st.error("فشل الاتصال بمزود البيانات. يرجى التحديث.")

if st.button('🔄 Force Update'): st.rerun()
