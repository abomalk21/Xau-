import streamlit as st
import yfinance as yf
from datetime import datetime
import pytz

# إعدادات الصفحة
st.set_page_config(page_title="XAU Hand-Radar", layout="centered")
ny_tz = pytz.timezone('America/New_York')
bg_tz = pytz.timezone('Asia/Baghdad')

st.title("🏹 XAU Hand-Radar")
st.write("اضغط على الزر أدناه لجلب السعر اللحظي بدقة السيلفر بوليت.")

# وظيفة جلب البيانات - طلب واحد مباشر عند الاستدعاء
def get_price_once():
    try:
        # استخدام الذهب الفوري XAUUSD=X لتقليل الفجوة السعرية
        data = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
        if not data.empty:
            last_p = float(data['Close'].iloc[-1])
            midnight_p = float(data['Open'].iloc[0])
            return last_p, midnight_p
        return None, None
    except:
        return None, None

# زر التحديث اليدوي لتجنب Server Busy
if st.button('🔄 تحديث السعر الآن (LIVE)'):
    with st.spinner('جاري جلب السعر من السوق...'):
        price, midnight = get_price_once()
        
        if price:
            now_ny = datetime.now(ny_tz)
            now_bg = datetime.now(bg_tz)
            
            # عرض السعر المباشر ومقارنته بمنتصف الليل
            st.metric("💰 سعر الذهب الحالي", f"{price:.2f}")
            
            if price > midnight:
                st.markdown(f"<div style='background-color:#ff4b4b; padding:20px; border-radius:10px; text-align:center;'> <h2 style='color:white;'>🔴 إشارة بيع (SELL)</h2> <p style='color:white;'>السعر أعلى من افتتاح منتصف الليل ({midnight:.2f})</p></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color:#28a745; padding:20px; border-radius:10px; text-align:center;'> <h2 style='color:white;'>🟢 إشارة شراء (BUY)</h2> <p style='color:white;'>السعر أدنى من افتتاح منتصف الليل ({midnight:.2f})</p></div>", unsafe_allow_html=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            col1.write(f"🇺🇸 توقيت نيويورك: `{now_ny.strftime('%H:%M:%S')}`")
            col2.write(f"🇮🇶 توقيت بغداد: `{now_bg.strftime('%H:%M:%S')}`")
        else:
            st.error("فشل الاتصال بالسيرفر. يرجى المحاولة مرة أخرى بعد ثوانٍ.")
else:
    st.info("بانتظار طلبك.. اضغط على الزر عند اقتراب شمعة السيلفر بوليت.")

st.warning("⚠️ ملاحظة: هذا الإصدار يدوي لضمان عدم توقف التطبيق أثناء التداول.")
