import streamlit as st
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")

# --- 2. KIỂM TRA THƯ VIỆN ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random
except ImportError as e:
    st.error(f"❌ LỖI: Thiếu thư viện. Hãy kiểm tra file requirements.txt.\nChi tiết: {e}")
    st.stop()

THOI_GIAN_MOI_CAU = 30

# --- 3. CSS GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        
        .gcpd-title {
            font-family: sans-serif; color: #002147; 
            font-size: 24px; font-weight: 900; text-align: center;
            text-transform: uppercase; margin-bottom: 20px;
        }
        
        /* Đồng hồ số */
        .timer-digital {
            font-size: 45px; font-weight: 900; color: #d32f2f;
            text-align: center; background-color: #ffebee;
            border: 2px solid #d32f2f; border-radius: 12px;
            width: 120px; margin: 0 auto 20px auto;
            padding: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Khung câu hỏi */
        .question-box {
            background-color: #ffffff; padding: 20px; border-radius: 10px;
            border: 2px solid #002147;
            font-size: 18px; font-weight: bold; color: #002147;
            margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        /* Khung
