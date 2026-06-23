import streamlit as st
import os

st.write("Files in data folder:")

if os.path.exists("data"):
    st.write(os.listdir("data"))
else:
    st.write("data folder not found")
