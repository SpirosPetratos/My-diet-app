import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Diet Tracker", layout="centered")

# --- API KEY ---
API_KEY = "AIzaSyA2VOGJj6BrrK8wG6RTEln5CVDKFIYoI_E"
genai.configure(api_key=API_KEY)

# ΑΥΤΟΜΑΤΗ ΕΠΙΛΟΓΗ ΜΟΝΤΕΛΟΥ ΓΙΑ ΑΠΟΦΥΓΗ 404
@st.cache_resource
def get_working_model():
    try:
        # Ψάχνουμε στη λίστα της Google για ένα μοντέλο που υποστηρίζει εικόνες
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name or 'gemini-pro-vision' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-1.5-flash') # Fallback
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# --- ΣΥΝΔΕΣΗ SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1")
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = load_data()

st.title("🥗 AI Food Tracker")
st.info(f"Συνδεδεμένο μοντέλο: {model.model_name}")

img_file = st.camera_input("Τράβα μια φωτό")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Ανάλυση..."):
        prompt = "Analyze food. Return ONLY a JSON object: {'item': 'name', 'p': 10, 'c': 10, 'f': 10, 'cal': 100}"
        
        try:
            response = model.generate_content([prompt, img])
            # Καθαρισμός κειμένου
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            # Μετατροπή σε JSON (αντικατάσταση μονών εισαγωγικών αν υπάρχουν)
            clean_txt = clean_txt.replace("'", '"')
            data = json.loads(clean_txt)
            
            # Αποθήκευση
            new_row = pd.DataFrame([data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.success("Καταγράφηκε!")
            st.rerun()
        except Exception as e:
            st.error(f"Σφάλμα Google: {e}")

# --- ΕΜΦΑΝΙΣΗ ΣΥΝΟΛΩΝ ---
if not df.empty:
    st.divider()
    for c in ['p', 'c', 'f', 'cal']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    
    st.metric("Συνολικές Θερμίδες", f"{int(df['cal'].sum())} kcal")
    col1, col2, col3 = st.columns(3)
    col1.metric("Πρωτεΐνη", f"{int(df['p'].sum())}g")
    col2.metric("Υδατ/κες", f"{int(df['c'].sum())}g")
    col3.metric("Λίπη", f"{int(df['f'].sum())}g")
    
    if st.button("Διαγραφή Δεδομένων (Reset)"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()
