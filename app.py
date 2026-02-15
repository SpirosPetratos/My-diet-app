import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ
st.set_page_config(page_title="AI Diet Tracker", page_icon="🥗")

# --- ΒΑΛΕ ΤΟ API KEY ΣΟΥ ΕΔΩ ---
API_KEY = "ΒΑΛΕ_ΕΔΩ_ΤΟ_API_KEY_ΣΟΥ" 
# ------------------------------

genai.configure(api_key=API_KEY)

# ΔΟΚΙΜΑΖΟΥΜΕ ΤΟ ΠΙΟ ΣΤΑΘΕΡΟ ΟΝΟΜΑ ΜΟΝΤΕΛΟΥ
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(worksheet="Sheet1")
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = get_data()

st.title("📸 AI Nutrition Tracker")

# 3. ΚΑΜΕΡΑ
img_file = st.camera_input("Βγάλε φωτό το φαγητό σου")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Το AI αναλύει..."):
        # Ζητάμε από το AI να μην βάλει markdown (```) για να μην μπερδευτεί το iPhone
        prompt = 'Identify the food. Return ONLY a JSON object: {"item": "όνομα", "p": 10, "c": 20, "f": 5, "cal": 150}. No other text.'
        
        try:
            response = model.generate_content([prompt, img])
            res_text = response.text.strip()
            
            # Καθαρισμός για το iPhone: βρίσκουμε το πρώτο { και το τελευταίο }
            start = res_text.find("{")
            end = res_text.rfind("}") + 1
            if start != -1 and end != 0:
                data = json.loads(res_text[start:end])
                
                # Αποθήκευση
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"Προστέθηκε: {data['item']}")
                st.rerun()
            else:
                st.error("Το AI δεν έστειλε σωστή μορφή δεδομένων.")
        except Exception as e:
            st.error(f"Σφάλμα: {e}")

# 4. ΕΜΦΑΝΙΣΗ ΣΥΝΟΛΩΝ
if not df.empty:
    st.divider()
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.header(f"🔥 {int(df['cal'].sum())} kcal")
    c1, c2, c3 = st.columns(3)
    c1.metric("Πρωτεΐνη", f"{int(df['p'].sum())}g")
    c2.metric("Υδατ/κες", f"{int(df['c'].sum())}g")
    c3.metric("Λίπη", f"{int(df['f'].sum())}g")

    if st.button("🚨 Μηδενισμός"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()
