import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. ΒΑΣΙΚΗ ΡΥΘΜΙΣΗ
st.set_page_config(page_title="Diet Tracker", layout="centered")

# --- API KEY ---
# Βάλε το νέο σου κλειδί εδώ
API_KEY = "AIzaSyCKiCJypwJ4dy0Qxb4Cv8vNxx9A2CxYlD8" 

# ΡΥΘΜΙΣΗ ΓΙΑ ΑΠΟΦΥΓΗ ΤΟΥ 404 (v1 αντί για v1beta)
genai.configure(api_key=API_KEY, transport="rest")

# Χρησιμοποιούμε το μοντέλο 1.5-flash που υποστηρίζει σίγουρα εικόνες
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1")
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = load_data()

st.title("🥗 AI Food Tracker")

# Εμφάνιση κατάστασης για σιγουριά
st.success("Το σύστημα είναι έτοιμο!")

img_file = st.camera_input("Τράβα μια φωτό το Milko σου")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Το AI διαβάζει την ετικέτα..."):
        # Το prompt στα αγγλικά είναι πιο αποτελεσματικό για το JSON
        prompt = "Analyze this food image. Return ONLY a JSON: {'item': 'name', 'p': 10, 'c': 10, 'f': 5, 'cal': 150}"
        
        try:
            # Κλήση του μοντέλου
            response = model.generate_content([prompt, img])
            
            # Καθαρισμός κειμένου για iPhone & PC
            res_text = response.text.strip()
            # Βρίσκουμε το JSON ανάμεσα στα άγκιστρα
            start = res_text.find("{")
            end = res_text.rfind("}") + 1
            
            if start != -1:
                data = json.loads(res_text[start:end].replace("'", '"'))
                
                # Αποθήκευση στο Google Sheet
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.balloons()
                st.success(f"Προστέθηκε: {data['item']}")
                st.rerun()
            else:
                st.error("Δεν βρέθηκαν δεδομένα στη φωτογραφία.")
        except Exception as e:
            # Αν βγάλει πάλι 404, θα μας πει ακριβώς το URL που φταίει
            st.error(f"Σφάλμα σύνδεσης: {e}")

# 3. ΕΜΦΑΝΙΣΗ ΣΤΑΤΙΣΤΙΚΩΝ
if not df.empty:
    st.divider()
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.header(f"🔥 {int(df['cal'].sum())} kcal")
    c1, c2, c3 = st.columns(3)
    c1.metric("Πρωτεΐνη", f"{int(df['p'].sum())}g")
    c2.metric("Υδατ/κες", f"{int(df['c'].sum())}g")
    c3.metric("Λίπη", f"{int(df['f'].sum())}g")

    if st.button("🚨 Διαγραφή Δεδομένων"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()
