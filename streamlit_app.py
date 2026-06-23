import streamlit as st
from PIL import Image

st.set_page_config(layout="wide")

st.title("Roof Leak Mapper")

# Load images from data folder
ceiling_img = Image.open("data/Office Ceiling (Roof).jpg")
roof_img = Image.open("data/Desk (under roof).jpg")

# Display side by side
col1, col2 = st.columns(2)

with col1:
    st.subheader("Ceiling Plan")
    st.image(ceiling_img, use_container_width=True)

with col2:
    st.subheader("Roof Plan")
    st.image(roof_img, use_container_width=True)
