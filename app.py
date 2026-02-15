import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. ΒΑΣΙΚΗ ΡΥΘΜΙΣΗ
st.set_page_config(page_title="Diet Tracker", layout="centered")

# --- API KEY ---
# Βάλε εδώ το κλειδί σου. Σιγουρέψου ότι δεν έχει κενά μέσα στα εισαγωγικά.
API_KEY = "AIzaSyB4Er7_2zt5W9A_jSrTbMqg2_rAlNlYFis" 

genai.configure(api_key=API_KEY)

# Επιλέγουμε το μοντέλο με το πλήρες όνομα για αποφυγή του σφάλματος 404
model = genai.GenerativeModel('models/gemini-1.5-flash')

# 2. ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Διαβάζει το Sheet1 από το Google Sheet σου
        df = conn.read(worksheet="Sheet1")
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = load_data()

st.title("🥗 AI Food Tracker")

# 3. ΛΕΙΤΟΥΡΓΙΑ ΚΑΜΕΡΑΣ
img_file = st.camera_input("Τράβα μια φωτογραφία του γεύματος")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Ανάλυση γεύματος..."):
        # Το prompt είναι απλό για να μην μπερδεύεται το JSON
        prompt = "Analyze this food image. Return ONLY a JSON object: {'item': 'name', 'p': 10, 'c': 10, 'f': 5, 'cal': 150}"
        
        try:
            # Κλήση του AI
            response = model.generate_content([prompt, img])
            
            # Καθαρισμός κειμένου για να παίζει σωστά και σε iPhone
            raw_text = response.text.strip()
            # Αφαιρούμε τυχόν markdown σύμβολα (```json)
            if "{" in raw_text:
                clean_json = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                # Αντικατάσταση μονών εισαγωγικών με διπλά για έγκυρο JSON
                clean_json = clean_json.replace("'", '"')
                data = json.loads(clean_json)
                
                # Αποθήκευση στο Google Sheet
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"Προστέθηκε: {data['item']}")
                st.rerun()
        except Exception as e:
            st.error(f"Πρόβλημα σύνδεσης: {e}")

# 4. ΕΜΦΑΝΙΣΗ ΣΤΑΤΙΣΤΙΚΩΝ
if not df.empty:
    st.divider()
    # Μετατροπή στηλών σε αριθμούς
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.header(f"🔥 {int(df['cal'].sum())} kcal")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Πρωτεΐνη", f"{int(df['p'].sum())}g")
    c2.metric("Υδατ/κες", f"{int(df['c'].sum())}g")
    c3.metric("Λίπη", f"{int(df['f'].sum())}g")

    # Κουμπί για Reset
    if st.button("🚨 Διαγραφή Όλων"):
        empty_df = pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])
        conn.update(worksheet="Sheet1", data=empty_df)
        st.rerun()
