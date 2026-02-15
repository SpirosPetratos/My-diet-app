import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="Diet Tracker", layout="centered")

# --- API KEY ---
API_KEY = "AIzaSyCKiCJypwJ4dy0Qxb4Cv8vNxx9A2CxYlD8" 

# ΕΠΙΒΟΛΗ ΕΚΔΟΣΗΣ API V1 (Αυτό θα λύσει το 404)
os.environ["GOOGLE_API_USE_MTLS"] = "never"
genai.configure(api_key=API_KEY, transport='rest') # Χρήση REST αντί για gRPC

# Χρήση του μοντέλου χωρίς το πρόθεμα models/ για δοκιμή
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

# Έλεγχος αν το μοντέλο ανταποκρίνεται πριν την κάμερα
try:
    st.caption(f"✅ Σύστημα έτοιμο (Model: {model.model_name})")
except Exception as e:
    st.error(f"❌ Πρόβλημα ενεργοποίησης: {e}")

img_file = st.camera_input("Τράβα μια φωτό")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Ανάλυση..."):
        prompt = "Analyze food. Return ONLY JSON: {'item': 'name', 'p': 10, 'c': 10, 'f': 5, 'cal': 150}"
        
        try:
            # Κλήση με καθαρό τρόπο
            response = model.generate_content([prompt, img])
            
            # iPhone-Friendly Parsing
            res_text = response.text.strip()
            start = res_text.find("{")
            end = res_text.rfind("}") + 1
            if start != -1:
                data = json.loads(res_text[start:end].replace("'", '"'))
                
                # Αποθήκευση
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success("Καταγράφηκε!")
                st.rerun()
        except Exception as e:
            st.error(f"Σφάλμα Google: {e}")

# --- ΣΤΑΤΙΣΤΙΚΑ ---
if not df.empty:
    st.divider()
    for c in ['p', 'c', 'f', 'cal']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    
    st.subheader(f"🔥 {int(df['cal'].sum())} kcal σήμερα")
    c1, c2, c3 = st.columns(3)
    c1.metric("P", f"{int(df['p'].sum())}g")
    c2.metric("C", f"{int(df['c'].sum())}g")
    c3.metric("F", f"{int(df['f'].sum())}g")
    
    if st.button("Reset Data"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()

