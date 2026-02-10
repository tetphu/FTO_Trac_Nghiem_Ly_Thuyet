import streamlit as st
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="FTO System",
    page_icon="🚓",
    layout="centered"
)

# --- 2. KIỂM TRA THƯ VIỆN & IMPORT ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random
except ImportError as e:
    st.error("LỖI: Thiếu thư viện. Hãy kiểm tra file requirements.txt")
    st.stop()

# --- 3. CSS GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        .gcpd-title {
            font-family: sans-serif; color: #002147; 
            font-size: 24px; font-weight: 900; text-align: center;
            text-transform: uppercase; margin-bottom: 10px;
        }
        .user-info {
            background-color: #e3f2fd; padding: 10px; border-radius: 8px;
            color: #0d47a1; font-weight: bold; text-align: center;
            margin-bottom: 10px; border: 1px solid #bbdefb;
        }
        .timer-digital {
            font-size: 45px; font-weight: 900; color: #d32f2f;
            text-align: center; background-color: #ffebee;
            border: 2px solid #d32f2f; border-radius: 12px;
            width: 120px; margin: 0 auto 20px auto; padding: 5px;
        }
        .question-box {
            background-color: #ffffff; padding: 20px; border-radius: 10px;
            border: 2px solid #002147;
            font-size: 18px; font-weight: bold; color: #002147; margin-bottom: 15px;
        }
        .explanation-box {
            background-color: #e8f5e9; padding: 15px;
            border-radius: 8px; border-left: 5px solid #4caf50;
            margin-top: 15px; color: #1b5e20;
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 12px !important;
        }
        div.row-widget.stRadio > div { flex-direction: row; justify-content: center; }
        </style>
    """, unsafe_allow_html=True)

# --- 4. KẾT NỐI DATABASE ---
def ket_noi_csdl
