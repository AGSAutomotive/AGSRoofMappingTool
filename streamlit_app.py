import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(layout="wide")
st.title("Roof Leak Mapping System (Stable Version)")

# -----------------------------
# PLANT SELECTION
# -----------------------------
plant = st.selectbox("Select Plant", ["Plant A", "Plant B", "Plant C"])

plant_data = {
    "Plant A": {
        "ceiling": "data/Office Ceiling (Roof).jpg",
        "roof": "data/Desk (under roof).jpg",
    },
    "Plant B": {
        "ceiling": "data/Office Ceiling (Roof).jpg",
        "roof": "data/Desk (under roof).jpg",
    },
    "Plant C": {
        "ceiling": "data/Office Ceiling (Roof).jpg",
        "roof": "data/Desk (under roof).jpg",
    },
}

# -----------------------------
# LOAD IMAGES
# -----------------------------
ceiling_img = Image.open(plant_data[plant]["ceiling"]).convert("RGB")
roof_img = Image.open(plant_data[plant]["roof"]).convert("RGB")

# -----------------------------
# SESSION STATE
# -----------------------------
if "leaks" not in st.session_state:
    st.session_state.leaks = {
        "Plant A": [],
        "Plant B": [],
        "Plant C": []
    }

# -----------------------------
# LAYOUT
# -----------------------------
col1, col2 = st.columns(2)

# -----------------------------
# CEILING IMAGE CLICK (NO CANVAS)
# -----------------------------
with col1:
    st.subheader("Click to Add Leak (X/Y)")

    # Show image
    st.image(ceiling_img, use_container_width=True)

    st.write("Manually enter leak position (temporary method):")

    x = st.number_input("X coordinate", min_value=0, max_value=ceiling_img.width, value=0)
    y = st.number_input("Y coordinate", min_value=0, max_value=ceiling_img.height, value=0)

    if st.button("Add Leak"):
        st.session_state.leaks[plant].append((x, y))

# -----------------------------
# ROOF DISPLAY
# -----------------------------
with col2:
    st.subheader("Roof Plan (Mapped Leaks)")

    img = roof_img.copy()
    draw = ImageDraw.Draw(img)

    for x, y in st.session_state.leaks[plant]:
        draw.ellipse((x-6, y-6, x+6, y+6), fill="red")

    st.image(img, use_container_width=True)

# -----------------------------
# DEBUG
# -----------------------------
st.write("Leaks:", st.session_state.leaks[plant])
