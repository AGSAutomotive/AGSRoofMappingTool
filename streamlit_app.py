import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(layout="wide")
st.title("Roof Leak Mapping System (Clickable)")

# -----------------------------
# PLANTS
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
# CLICKABLE CEILING
# -----------------------------
with col1:
    st.subheader("Click Ceiling to Add Leak")

    coords = streamlit_image_coordinates(
        ceiling_img,
        key=plant
    )

    if coords:
        x, y = coords["x"], coords["y"]

        if len(st.session_state.leaks[plant]) == 0 or st.session_state.leaks[plant][-1] != (x, y):
            st.session_state.leaks[plant].append((x, y))

# -----------------------------
# ROOF OUTPUT
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
st.write("Leak points:", st.session_state.leaks[plant])
