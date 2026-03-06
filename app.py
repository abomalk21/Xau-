import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime
import time
import plotly.graph_objects as go

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Gold Anti-Trap Pro", layout="wide")

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

# --- جلب بيانات الذهب والدولار معاً لضمان عدم الخداع ---
@st.cache_data(ttl=60)
def get_market_data():
    try:
        gold = yf.download("GC=F", period="1d", interval="15m", progress=False, auto_adjust=True)
        dxy = yf.download("DX-Y", period="1d", interval="15m", progress=False, auto_adjust=True)
        if not gold.empty:
            gold.index = gold.index.tz_convert(ny_tz)
        if not dxy.empty:
            dxy.index = dxy.index.tz_convert(ny_tz)
        return gold, dxy
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- دالة تحليل المصائد (Anti-Trap Logic) ---
def analyze_traps(gold_df, dxy_df, m):
    traps = []
    if gold_df.empty or dxy_df.empty: return traps
    
    # 1. كشف SMT (تفاوت القوة مع الدولار)
    g_move = gold_df['Close'].iloc[-1] - gold_df['Close'].iloc[-3]
    d_move = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-3]
    if g_move > 0 and d_move > 0:
        traps.append("⚠️ SMT Warning: الذهب والدولار يصعدان معاً (احتمال كسر كاذب)")
    
    # 2. كشف سحب السيولة (Liquidity Sweep)
    if m['latest'] > m['london_h'] and m['london_h'] > 0:
        traps.append("🔍 Liquidity Sweep: السعر فوق قمة لندن (راقب الانعكاس)")
    if m['latest'] < m['london_l'] and m['london_l'] > 0:
        traps.append("🔍 Liquidity Sweep: السعر تحت قاع لندن (راقب الارتداد)")
        
    return traps

# --- حساب المقاييس الرئيسية ---
def get_metrics(df):
    if df.empty: return None
    now_ny = datetime.now(ny_tz)
    mid_df = df[df.index.date == now_ny.date()].between_time('00:00', '00:15')
    mn_open = mid_df['Open'].iloc[0] if not mid_df.empty else df['Open'].iloc[0]
    asia = df.between_time("20:00", "00:00")
    london = df.between_time("02:00", "05:00")
    return {
        "latest": float(df['Close'].iloc[-1]),
        "mn_open": float(mn_open),
        "asia_h": float(asia['High'].max()) if not asia.empty else 0,
        "asia_l": float(asia['Low'].min()) if not asia.empty else 0,
        "london_h": float(london['High'].max()) if not london.empty else 0,
        "london_l": float(london['Low'].min()) if not london.empty else 0,
        "df_plot": df.tail(40)
    }

# --- العرض الرئيسي ---
st.title("🛡️ رادار الذهب - نسخة الحماية من الخداع")
main_placeholder = st.empty()

while True:
    with main_placeholder.container():
        g_df, d_df = get_market_data()
        m = get_metrics(g_df)
        
        if m:
            # الصف الأول: البيانات السعرية
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Gold Price", f"{m['latest']:.2f}")
            c2.metric("🎯 Midnight Open", f"{m['mn_open']:.2f}")
            c3.metric("🇺🇸 NY Time", datetime.now(ny_tz).strftime("%H:%M"))
            c4.metric("🇮🇶 Baghdad", datetime.now(bg_tz).strftime("%H:%M"))

            # تحليل المخاطر (صندوق التحذيرات)
            traps = analyze_traps(g_df, d_df, m)
            if traps:
                for t in traps: st.warning(t)
            else:
                st.info("✅ لا توجد مصائد واضحة حالياً - الهيكل متناغم")

            # الشارت المزدوج (ذهب + دولار)
            col_chart, col_dxy = st.columns([3, 1])
            with col_chart:
                fig = go.Figure(data=[go.Candlestick(x=m['df_plot'].index, open=m['df_plot']['Open'], 
                                                     high=m['df_plot']['High'], low=m['df_plot']['Low'], 
                                                     close=m['df_plot']['Close'], name="Gold")])
                fig.add_hline(y=m['mn_open'], line_dash="dash", line_color="white", annotation_text="Midnight")
                fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            with col_dxy:
                st.write("DXY Trend (15m)")
                st.line_chart(d_df['Close'].tail(20), height=350)

            # بيانات السيولة في الأسفل
            st.divider()
            b1, b2 = st.columns(2)
            b1.write(f"🇬🇧 **London:** High {m['london_h']:.2f} | Low {m['london_l']:.2f}")
            b2.write(f"🌏 **Asia:** High {m['asia_h']:.2f} | Low {m['asia_l']:.2f}")
        else:
            st.info("جاري تحديث البيانات...")

    time.sleep(60)
    st.rerun()
