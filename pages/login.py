from utils import load_css
load_css("style/style.css")

import streamlit as st

st.title("Login to Dravyum")

username = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if username == "admin" and password == "1234":
        st.success("Login successful!")
        st.session_state['logged_in'] = True
    else:
        st.error("Invalid credentials")
