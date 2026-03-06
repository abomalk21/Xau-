import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime
import plotly.graph_objects as go

# --- إعدادات الواجهة السريعة ---
st.set_page_config(page_title="XAU", layout="wide") # تغيير اسم المتصفح إلى XAU

ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

# دالة جلب البيانات المدمجة لسرعة الاستجابة
@st.cache_data(ttl=60)
def get_market_data():
    try:
        # جلب الذهب والدولار معاً لتقليل زمن التأخير
        data = yf.download("GC=F DX-Y", period="1d", interval="15m", progress=False, auto_adjust=True)
        if data.empty: return pd.DataFrame(), pd.DataFrame()
        
        gold = data.xs('GC=F', axis=1, level=1)
        dxy = data.xs('DX-Y', axis=1, level=1)
        
        gold.index = gold.index.tz_convert(ny_tz)
        return gold, dxy
    except:
        return pd.DataFrame(), pd.DataFrame()

# العنوان المختصر
st.title("🏆 XAU") # تغيير اسم التطبيق الرئيسي

try:
    g_df, d_df = get_market_data()
    
    if not g_df.empty
