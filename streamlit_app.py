import streamlit as st
from PIL import Image, ImageDraw
import base64
import io

# If canvas is installed correctly
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide")
st.title("Roof Leak Mapping System")

# -----------------------------
# PLANT SELECTION
# -----------------------------
plant = st.selectbox("Select Manufacturing Plant", ["Plant A", "Plant B", "Plant C"])

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
# CONVERT IMAGE → BASE64 (FIX FOR CANVAS)
# -----------------------------
def pil_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return "data:image/png;base64," + encoded

ceiling_base64 = pil_to_base64(ceiling_img)

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
# CEILING (CLICKABLE CANVAS)
# -----------------------------
with col1:
    st.subheader("Click Ceiling to Mark Leak")

    canvas_result = st_canvas(
        background_image=ceiling_base64,
        drawing_mode="point",
        height=500,
        width=500,
        key=plant
    )

    # Capture clicks
    if canvas_result.json_data:
        objects = canvas_result.json_data["objects"]

        if objects:
            last = objects[-1]
            x = last["left"]
            y = last["top"]

            # prevent duplicates
            if len(st.session_state.leaks[plant]) == 0 or st.session_state.leaks[plant][-1] != (x, y):
                st.session_state.leaks[plant].append((x, y))

# -----------------------------
# ROOF (MAPPED OUTPUT)
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
