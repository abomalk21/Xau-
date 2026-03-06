import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta

# --- الإعدادات ---
ny_tz = pytz.timezone('America/New_York')

st.set_page_config(page_title="XAU Ultra-Live", layout="wide")

# تقليل الكاش إلى ثانية واحدة فقط لمحاكاة السعر المباشر
@st.cache_data(ttl=1) 
def get_spot_gold():
    try:
        # استخدام الرمز الفوري بدلاً من العقود الآجلة
        df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
        return df
    except: return None

data = get_spot_gold()

if data is not None and not data.empty:
    now_ny = datetime.now(ny_tz)
    # السعر الفوري المباشر
    last_p = float(data['Close'].iloc[-1])
    # سعر افتتاح منتصف الليل الفعلي
    mn_val = float(data['Open'].iloc[0]) 

    # 1. إشارة التداول الحاشمة (Logic)
    if last_p > mn_val:
        st.error(f"🔴 SELL SIGNAL | Price {last_p:.2f} is ABOVE Midnight")
    else:
        st.success(f"🟢 BUY SIGNAL | Price {last_p:.2f} is BELOW Midnight")

    # 2. مراقبة مستويات السيولة (London & Asia)
    # ملاحظة: هذه المستويات رقمية بحتة لتجنب انهيار السيرفر
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💰 Live Spot")
        st.title(f"{last_p:.2f}")
        
    with col2:
        st.subheader("🎯 Midnight")
        st.title(f"{mn_val:.2f}")

    with col3:
        # عداد الثواني للسيلفر بوليت
        target_h = 10 if now_ny.hour < 10 else 14
        target_time = now_ny.replace(hour=target_h, minute=0, second=0, microsecond=0)
        if now_ny.hour >= 14: target_time += timedelta(days=1)
        
        diff = target_time - now_ny
        st.subheader("🏹 Next SB")
        st.title(f"{diff.seconds//3600:02d}:{(diff.seconds//60)%60:02d}:{diff.seconds%60:02d}")

    # 3. تنبيهات كسر المستويات
    st.info("💡 Tip: Use this tool for DIRECTION and your broker for EXECUTION.")

else:
    st.warning("🔄 Server Busy - Refreshing Connection...")
    st.rerun()
