import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. API & Σελίδα
st.set_page_config(page_title="AI Diet Tracker", page_icon="🥗")
API_KEY = "AIzaSyA2VOGJj6BrrK8wG6RTEln5CVDKFIYoI_E" # <--- ΒΑΛΕ ΤΟ ΚΛΕΙΔΙ ΣΟΥ
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Σύνδεση με Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(worksheet="Sheet1")
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal'])

df = get_data()

st.title("📸 AI Nutrition Tracker")

# 3. Κάμερα
img_file = st.camera_input("Βγάλε φωτό το φαγητό")

if img_file:
    img = Image.open(img_file)
    with st.spinner("Το AI αναλύει..."):
        prompt = 'Analyze food. Return ONLY JSON: {"item": "name", "p": 10, "c": 20, "f": 5, "cal": 150}'
        response = model.generate_content([prompt, img])
        data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group())

        # Αποθήκευση
        new_row = pd.DataFrame([data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success(f"Προστέθηκε: {data['item']}")
        st.rerun()

# 4. Εμφάνιση Συνολικών
if not df.empty:
    st.divider()
    for col in ['p', 'c', 'f', 'cal']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.subheader(f"🔥 Σύνολο: {int(df['cal'].sum())} kcal")
    c1, c2, c3 = st.columns(3)
    c1.metric("Πρωτεΐνη", f"{int(df['p'].sum())}g")
    c2.metric("Υδατ/κες", f"{int(df['c'].sum())}g")
    c3.metric("Λίπη", f"{int(df['f'].sum())}g")

    if st.button("Μηδενισμός Ημέρας"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=['item', 'p', 'c', 'f', 'cal']))
        st.rerun()
