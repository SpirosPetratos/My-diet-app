import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Diet Tracker", layout="centered")

# --- API KEY ---
# Βάλε το ΟΛΟΚΑΙΝΟΥΡΓΙΟ κλειδί που έβγαλες
API_KEY = "AIzaSyCKiCJypwJ4dy0Qxb4Cv8vNxx9A2CxYlD8" 
genai.configure(api_key=API_KEY)

# Χρησιμοποιούμε το 1.5-flash που είναι το μόνο που υποστηρίζει πλέον φωτό σωστά
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
st.success("Σύνδεση επιτυχής! Τράβα μια φωτογραφία.")

img_file = st.camera_input("Βγάλε φωτό το Milko ή το φαγητό σου")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Το AI αναλύει τη φωτογραφία..."):
        # Το prompt πρέπει να είναι ξεκάθαρο
        prompt = "Analyze this food/drink image. Return ONLY a JSON object: {'item': 'name', 'p': 10, 'c': 10, 'f': 5, 'cal': 150}"
        
        try:
            # Εδώ είναι το μυστικό: στέλνουμε το prompt και την εικόνα μαζί
            response = model.generate_content([prompt, img])
            
            # Καθαρισμός του κειμένου για αποφυγή σφαλμάτων στο iPhone
            res_text = response.text.strip()
            if "{" in res_text:
                json_part = res_text[res_text.find("{"):res_text.rfind("}")+1]
                data = json.loads(json_part.replace("'", '"'))
                
                # Αποθήκευση στο Google Sheet
                new_row = pd.DataFrame([data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.balloons()
                st.success(f"Προστέθηκε: {data['item']}")
                st.rerun()
            else:
                st.error("Το AI δεν μπόρεσε να αναγνωρίσει το προϊόν. Δοκίμασε πιο κοντά.")
        except Exception as e:
            st.error(f"Σφάλμα Google: {e}")

# --- ΕΜΦΑΝΙΣΗ ΣΥΝΟΛΩΝ ---
if not df.empty:
    st.divider()
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.header(f"🔥 Σύνολο: {int(df['cal'].sum())} kcal")
    col1, col2, col3 = st.columns(3)
    col1.metric("Πρωτεΐνη", f"{int(df['p'].sum())}g")
    col2.metric("Υδατ/κες", f"{int(df['c'].sum())}g")
    col3.metric("Λίπη", f"{int(df['f'].sum())}g")
    
    if st.button("🚨 Reset (Διαγραφή όλων)"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()
