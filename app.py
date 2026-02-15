import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ
st.set_page_config(page_title="AI Diet Tracker", page_icon="🥗")

# --- ΠΡΟΣΟΧΗ: ΒΑΛΕ ΤΟ ΚΛΕΙΔΙ ΣΟΥ ΕΔΩ ---
API_KEY = "AIzaSyA2VOGJj6BrrK8wG6RTEln5CVDKFIYoI_E" 
# ----------------------------------------

# Ρύθμιση του AI
genai.configure(api_key=API_KEY)
# Χρήση του πιο σταθερού μοντέλου για αποφυγή του NotFound Error
model = genai.GenerativeModel('gemini-1.5-flash-latest')

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
    with st.spinner("Το AI αναλύει το πιάτο..."):
        # Εντολή προς το AI - Ζητάμε καθαρό κείμενο χωρίς markdown για να μην μπερδεύεται ο Safari
        prompt = 'Analyze this food. Return ONLY a plain JSON object (no markdown, no backticks): {"item": "name", "p": 10, "c": 20, "f": 5, "cal": 150}'
        
        try:
            response = model.generate_content([prompt, img])
            
            # Καθαρισμός απάντησης για μέγιστη συμβατότητα με iPhone
            raw_text = response.text.strip()
            if "{" in raw_text and "}" in raw_text:
                start = raw_text.find("{")
                end = raw_text.rfind("}") + 1
                json_str = raw_text[start:end]
                data = json.loads(json_str)
                
                # Αποθήκευση
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"Προστέθηκε: {data['item']}")
                st.rerun()
            else:
                st.error("Το AI δεν επέστρεψε σωστά δεδομένα. Δοκίμασε ξανά.")
                
        except Exception as e:
            st.error(f"Σφάλμα: {e}")

# 4. ΕΜΦΑΝΙΣΗ ΣΥΝΟΛΩΝ
if not df.empty:
    st.divider()
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.header("📊 Σύνολα Ημέρας")
    
    t_cal = int(df['cal'].sum())
    t_p = int(df['p'].sum())
    t_c = int(df['c'].sum())
    t_f = int(df['f'].sum())

    st.subheader(f"🔥 {t_cal} kcal")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Πρωτεΐνη", f"{t_p}g")
    col2.metric("Υδατ/κες", f"{t_c}g")
    col3.metric("Λίπη", f"{t_f}g")

    with st.expander("Ιστορικό Γευμάτων"):
        st.table(df[['item', 'cal', 'p', 'c', 'f']])

    if st.button("🚨 Μηδενισμός Όλων"):
        empty_df = pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])
        conn.update(worksheet="Sheet1", data=empty_df)
        st.rerun()
