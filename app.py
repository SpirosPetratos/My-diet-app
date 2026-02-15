import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Diet Tracker", layout="centered")

# --- API KEY ---
# Δοκίμασε να το βάλεις ΧΩΡΙΣ κενά πριν ή μετά
raw_api_key = "AIzaSyCKiCJypwJ4dy0Qxb4Cv8vNxx9A2CxYlD8"
API_KEY = raw_api_key.strip()

genai.configure(api_key=API_KEY)

# ΑΛΛΑΓΗ ΜΟΝΤΕΛΟΥ ΣΕ 1.0 PRO (Το πιο σταθερό για Ευρώπη)
@st.cache_resource
def load_model():
    # Δοκιμάζουμε πρώτα το Pro Vision που είναι το πιο σίγουρο για φωτό
    return genai.GenerativeModel('gemini-pro-vision')

try:
    model = load_model()
except:
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- ΣΥΝΔΕΣΗ SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(worksheet="Sheet1").dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = load_data()

st.title("🥗 AI Food Tracker")
st.caption(f"Συνδεδεμένο μοντέλο: {model.model_name}")

img_file = st.camera_input("Τράβα μια φωτό")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Ανάλυση..."):
        # Το prompt πρέπει να είναι στα Αγγλικά για το Gemini 1.0
        prompt = "Analyze this food image. Provide calories, protein, carbs, and fat. Return ONLY a JSON object: {'item': 'food name', 'p': 10, 'c': 10, 'f': 5, 'cal': 150}"
        
        try:
            # Σημαντικό: Για το gemini-pro-vision η σύνταξη είναι ελαφρώς διαφορετική
            response = model.generate_content([prompt, img])
            res_text = response.text
            
            # Καθαρισμός JSON (για να παίζει και στο iPhone)
            start = res_text.find("{")
            end = res_text.rfind("}") + 1
            json_str = res_text[start:end].replace("'", '"')
            data = json.loads(json_str)
            
            # Αποθήκευση
            new_row = pd.DataFrame([data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.success("Έγινε!")
            st.rerun()
        except Exception as e:
            st.error(f"Σφάλμα: {e}")

# --- ΕΜΦΑΝΙΣΗ ΣΥΝΟΛΩΝ ---
if not df.empty:
    st.divider()
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.metric("Σύνολο Θερμίδων", f"{int(df['cal'].sum())} kcal")
    col1, col2, col3 = st.columns(3)
    col1.metric("P", f"{int(df['p'].sum())}g")
    col2.metric("C", f"{int(df['c'].sum())}g")
    col3.metric("F", f"{int(df['f'].sum())}g")
    
    if st.button("Reset"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()
