import streamlit as st
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas

st.title("Roof Leak Mapper")

plant = st.selectbox("Select Plant", ["Plant A", "Plant B", "Plant C"])

plant_data = {
    "Plant A": {"ceiling": "data/plant_a_ceiling.png", "roof": "data/plant_a_roof.png"},
    #"Plant B": {"ceiling": "data/plant_b_ceiling.png", "roof": "data/plant_b_roof.png"},
    #"Plant C": {"ceiling": "data/plant_c_ceiling.png", "roof": "data/plant_c_roof.png"},
}

ceiling_img = Image.open(plant_data[plant]["ceiling"]).convert("RGB")
roof_img = Image.open(plant_data[plant]["roof"]).convert("RGB")

# reset leaks when plant changes
if "active_plant" not in st.session_state or st.session_state.active_plant != plant:
    st.session_state.leaks = []
    st.session_state.active_plant = plant

col1, col2 = st.columns(2)

with col1:
    st.subheader("Ceiling (Click Leak Location)")

    canvas = st_canvas(
        background_image=ceiling_img,
        drawing_mode="point",
        height=500,
        width=500,
        key=plant
    )

    if canvas.json_data:
        objs = canvas.json_data["objects"]
        if objs:
            last = objs[-1]
            x, y = last["left"], last["top"]

            # prevent duplicates
            if not st.session_state.leaks or st.session_state.leaks[-1] != (x, y):
                st.session_state.leaks.append((x, y))

with col2:
    st.subheader("Roof (Mapped)")

    img = roof_img.copy()
    draw = ImageDraw.Draw(img)

    for x, y in st.session_state.leaks:
        draw.ellipse((x-6, y-6, x+6, y+6), fill="red")

    st.image(img)

st.write("Leak points:", st.session_state.leaks)


