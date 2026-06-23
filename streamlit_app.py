import streamlit as st
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide")
st.title("Roof Leak Mapping System")

# -----------------------------
# PLANT SELECTOR
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
# SESSION STATE (per plant leaks)
# -----------------------------
if "leaks" not in st.session_state:
    st.session_state.leaks = {
        "Plant A": [],
        "Plant B": [],
        "Plant C": []
    }

# -----------------------------
# RESET ON PLANT CHANGE
# -----------------------------
if "active_plant" not in st.session_state:
    st.session_state.active_plant = plant

if st.session_state.active_plant != plant:
    st.session_state.active_plant = plant

# -----------------------------
# LAYOUT
# -----------------------------
col1, col2 = st.columns(2)

# -----------------------------
# CEILING (CLICKABLE)
# -----------------------------
with col1:
    st.subheader("Click Ceiling to Mark Leak")

    canvas_result = st_canvas(
        background_image=ceiling_img,
        drawing_mode="point",
        height=500,
        width=500,
        key=plant
    )

    if canvas_result.json_data:
        objects = canvas_result.json_data["objects"]

        if objects:
            last = objects[-1]
            x = last["left"]
            y = last["top"]

            # prevent duplicate spam clicks
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
# DEBUG (optional)
# -----------------------------
st.write("Leak points:", st.session_state.leaks[plant])
