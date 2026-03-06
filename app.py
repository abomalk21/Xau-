import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime
import plotly.graph_objects as go

# --- إعدادات الواجهة ---
st.set_page_config(page_title="XAU", layout="wide")

ny_tz = pytz.timezone('America/New_York')

@st.cache_data(ttl=60)
def get_xau_data():
    try:
        # جلب الذهب والدولار معاً
        data = yf.download("GC=F DX-Y", period="1d", interval="15m", progress=False, auto_adjust=True)
        if data.empty:
            return None, None
        gold = data.xs('GC=F', axis=1, level=1)
        dxy = data.xs('DX-Y', axis=1, level=1)
        if not gold.empty:
            gold.index = gold.index.tz_convert(ny_tz)
        return gold, dxy
    except:
        return None, None

# --- العرض ---
st.title("🏆 XAU")

g_df, d_df = get_xau_data()

if g_df is not None and len(g_df) >= 1:
    latest_g = float(g_df['Close'].iloc[-1])
    now_ny = datetime.now(ny_tz)
    
    # حساب Midnight Open
    mid_df = g_df[g_df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = float(mid_df['Open'].iloc[0]) if not mid_df.empty else float(g_df['Open'].iloc[0])

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Gold", f"{latest_g:.2f}")
    col2.metric("🎯 Midnight", f"{mn_open:.2f}")
    col3.metric("🇺🇸 NY Time", now_ny.strftime("%H:%M"))

    if latest_g < mn_open:
        st.success("🟢 BUY ZONE")
    else:
        st.error("🔴 SELL ZONE")

    # الشارت
    fig = go.Figure(data=[go.Candlestick(
        x=g_df.index[-40:], open=g_df['Open'][-40:], high=g_df['High'][-40:],
        low=g_df['Low'][-40:], close=g_df['Close'][-40:], name="XAU"
    )])
    fig.add_hline(y=mn_open, line_dash="dash", line_color="white", annotation_text="MN Open")
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # حل مشكلة IndexError (التأكد من وجود شمعتين للمقارنة)
    if len(g_df) >= 2 and d_df is not None and len(d_df) >= 2:
        g_move = g_df['Close'].iloc[-1] - g_df['Close'].iloc[-2]
        d_move = d_df['Close'].iloc[-1] - d_df['Close'].iloc[-2]
        if g_move > 0 and d_move > 0:
            st.warning("⚠️ SMT Warning: الذهب والدولار يصعدان معاً")
    else:
        st.info("Market Opening: Waiting for more data bars...")

else:
    st.info("جاري تحديث البيانات...")

if st.button('🔄 Update'):
    st.rerun()
