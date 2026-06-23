import sys
import types

# 1. MONKEY-PATCH: Fix the streamlit-drawable-canvas version error
import streamlit.elements.lib.image_utils as image_utils
try:
    import streamlit.elements.image as st_image
    st_image.image_to_url = image_utils.image_to_url
except (ImportError, AttributeError):
    # Dynamically inject the module if it doesn't exist natively
    mod = types.ModuleType("streamlit.elements.image")
    mod.image_to_url = image_utils.image_to_url
    sys.modules["streamlit.elements.image"] = mod

import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click anywhere on the inner ceiling map to mark a leak. The corresponding location will automatically calculate and display on the roof view.")

---

# 2. Plant Selection Configuration
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# Define paths based on your uploaded files
# (Using your actual file names from your data folder)
if plant == "Plant 1":
    ceiling_path = "data/Office Ceiling (Roof).jpg"
    roof_path = "data/Desk (under roof).jpg"
elif plant == "Plant 2":
    # Fallback to the same files for demonstration until you upload unique plant images
    ceiling_path = "data/Office Ceiling (Roof).jpg"
    roof_path = "data/Desk (under roof).jpg"
else:
    ceiling_path = "data/Office Ceiling (Roof).jpg"
    roof_path = "data/Desk (under roof).jpg"

# 3. Safely Load and Resize Images to Match Nicely
try:
    ceiling_img = Image.open(ceiling_path)
    roof_img = Image.open(roof_path)
    
    # We fix a display width to prevent any image cutting off or misalignment
    DISPLAY_WIDTH = 600
    
    # Calculate aspect ratio based scaling
    c_width, c_height = ceiling_img.size
    scale_ratio = DISPLAY_WIDTH / float(c_width)
    display_height = int(float(c_height) * float(scale_ratio))
    
    # Resize both for clean parallel canvas layout
    ceiling_resized = ceiling_img.resize((DISPLAY_WIDTH, display_height))
    roof_resized = roof_img.resize((DISPLAY_WIDTH, display_height))

except FileNotFoundError:
    st.error(f"⚠️ Could not find the image files in the 'data/' folder. Please ensure 'Office Ceiling (Roof).jpg' and 'Desk (under roof).jpg' exist inside your repository.")
    st.stop()

---

# 4. Create Side-by-Side App Interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("📸 Inside Ceiling View (Click Here)")
    
    # Interactive clickable canvas layer
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",  # semi-transparent red
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=ceiling_resized,
        update_streamlit=True,
        height=display_height,
        width=DISPLAY_WIDTH,
        drawing_mode="point", # simple dot click mapping
        point_display_radius=6,
        key=f"canvas_{plant}"
    )

with col2:
    st.subheader("🦅 Corresponding Roof Map View")
    
    # Process clicks if user registers any coordinates
    if canvas_result.image_data is not None and len(canvas_result.json_data["objects"]) > 0:
        # Pull the absolute last click coordinates made by user
        last_object = canvas_result.json_data["objects"][-1]
        x_click = last_object["left"]
        y_click = last_object["top"]
        
        # Draw a targeting reticle or point over the roof image at identical relative space
        roof_output = roof_resized.copy()
        draw = ImageDraw.Draw(roof_output)
        
        # Draw a crosshair/circle highlighting the matching leak spot
        radius = 12
        draw.ellipse(
            (x_click - radius, y_click - radius, x_click + radius, y_click + radius), 
            outline="cyan", 
            width=4
        )
        draw.ellipse(
            (x_click - 3, y_click - 3, x_click + 3, y_click + 3), 
            fill="red"
        )
        
        st.image(roof_output, use_container_width=True)
        st.success(f"📍 Leak mapped coordinates relative to layout: X={int(x_click)}, Y={int(y_click)}")
    else:
        # Base fallback view before any click triggers
        st.image(roof_resized, use_container_width=True)
        st.info("💡 Click a leak location on the Left Ceiling Image to view its position on the Roof.")
