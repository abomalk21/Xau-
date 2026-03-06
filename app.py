import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- إعدادات سريعة ---
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')
st.set_page_config(page_title="Xau", layout="wide")

@st.cache_data(ttl=30) # تقليل وقت الكاش لسرعة التحديث
def get_fast_data():
    try:
        # سحب الذهب والدولار في طلب واحد لتقليل زمن الانتظار
        data = yf.download(["GC=F", "DX-Y"], period="2d", interval="15m", progress=False, group_by='ticker')
        if data.empty: return None, None
        
        g_df = data['GC=F'].dropna()
        d_df = data['DX-Y'].dropna()
        
        g_df.index = g_df.index.tz_convert(ny_tz)
        return g_df, d_df
    except: return None, None

st.title("🚀 XAU FAST RADAR")

g_df, d_df = get_fast_data()

if g_df is not None and not g_df.empty and len(d_df) > 0:
    now_ny = datetime.now(ny_tz)
    latest_g = g_df['Close'].iloc[-1]
    latest_d = d_df['Close'].iloc[-1]

    # 1. تنبيه الأخبار (سريع وبصري)
    st.error("⚠️ **HIGH VOLATILITY:** NFP/Jobs Report today at 08:30 AM NY Time.")

    # 2. عدادات علوية فائقة السرعة
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Gold", f"{latest_g:.2f}")
    
    # حساب Midnight بسرعة
    mn_price = g_df.between_time('00:00', '00:15')['Open'].iloc[0] if not g_df.between_time('00:00', '00:15').empty else g_df['Open'].iloc[0]
    c2.metric("🎯 Midnight", f"{mn_price:.2f}")
    
    # عداد الشمعة والسلفر بوليت (عمليات حسابية محلية سريعة)
    c3.metric("⏳ Bar Ends", f"{14 - (now_ny.minute % 15):02d}:{59 - now_ny.second:02d}")
    
    sb_target = next((now_ny.replace(hour=h, minute=0, second=0) for h in [3, 10, 14] if now_ny.replace(hour=h, minute=0, second=0) > now_ny), now_ny.replace(hour=3, minute=0, second=0) + timedelta(days=1))
    sb_diff = sb_target - now_ny
    c4.metric("🏹 Next SB", f"{sb_diff.seconds // 3600:02d}h {(sb_diff.seconds // 60) % 60:02d}m")

    # 3. الشارت (أداء محسّن)
    fig = go.Figure(data=[go.Candlestick(x=g_df.tail(100).index, open=g_df.tail(100)['Open'], high=g_df.tail(100)['High'], low=g_df.tail(100)['Low'], close=g_df.tail(100)['Close'])])
    
    # توحيد مستويات آسيا ولندن (أصفر منقط)
    for start, end, lbl in [("20:00", "00:00", "ASIA"), ("02:00", "05:00", "LONDON")]:
        sess = g_df.between_time(start, end)
        if not sess.empty:
            fig.add_hline(y=sess['High'].max(), line_color="yellow", line_dash="dot", annotation_text=f"{lbl} H")
            fig.add_hline(y=sess['Low'].min(), line_color="yellow", line_dash="dot", annotation_text=f"{lbl} L")
    
    fig.add_hline(y=mn_price, line_color="red", line_width=2, annotation_text="MIDNIGHT")
    fig.update_layout(template="plotly_dark", height=650, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) # إخفاء الشريط لزيادة السرعة

    # 4. سطر DXY والتوقيت في الأسفل
    st.markdown(f"📈 **DXY Index:** `{latest_d:.3f}` | 🇮🇶 **Baghdad:** `{datetime.now(bg_tz).strftime('%H:%M')}` | 🇺🇸 **NY:** `{now_ny.strftime('%H:%M')}`")

else:
    st.button("🔄 Data is loading... Click to Force Refresh")

if st.button('🚀 Quick Update'): st.rerun()
