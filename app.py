import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Diet Tracker")

# --- API KEY ---
API_KEY = "AIzaSyCKiCJypwJ4dy0Qxb4Cv8vNxx9A2CxYlD8" 
genai.configure(api_key=API_KEY, transport="rest")

# Χρήση του 1.5-flash
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ΣΥΝΔΕΣΗ SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(worksheet="Sheet1").dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = get_data()

st.title("🥗 AI Food Tracker")

# 1. ΚΟΥΜΠΙ ΕΛΕΓΧΟΥ (Πάτα το να δεις αν γράφει Success)
if st.button("Έλεγχος Σύνδεσης"):
    try:
        res = model.generate_content("Είσαι έτοιμος;")
        st.success(f"✅ Success: {res.text}")
    except Exception as e:
        st.error(f"❌ Σφάλμα: {e}")

# 2. ΚΑΜΕΡΑ
img_file = st.camera_input("Τράβα φωτό")

if img_file:
    # Μετατροπή της εικόνας σε μορφή που ΔΕΝ βγάζει 404
    img = Image.open(img_file)
    
    with st.spinner("Αναλύω..."):
        try:
            # ΝΕΟΣ ΤΡΟΠΟΣ ΑΠΟΣΤΟΛΗΣ (Αναγκαστικό Format)
            prompt = "Analyze food. Return ONLY JSON: {'item': 'name', 'cal': 100, 'p': 5, 'c': 5, 'f': 5}"
            
            # Εδώ αλλάζουμε το πώς στέλνουμε τα δεδομένα
            response = model.generate_content(
                contents=[
                    {"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": img_file.getvalue()}}]}
                ]
            )
            
            # Parsing (συμβατό με iPhone)
            raw = response.text
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1:
                data = json.loads(raw[start:end].replace("'", '"'))
                
                # Save to Sheets
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"Καταγράφηκε: {data['item']}")
                st.rerun()
            else:
                st.error("Το AI δεν επέστρεψε JSON. Δοκίμασε ξανά.")

        except Exception as e:
            st.error(f"Σφάλμα 404/POST: {e}")
            st.info("Αν βλέπεις 404, δοκίμασε να φτιάξεις ένα API Key από άλλο Google account (Gmail).")

# 3. ΠΙΝΑΚΑΣ
if not df.empty:
    st.divider()
    st.dataframe(df)
