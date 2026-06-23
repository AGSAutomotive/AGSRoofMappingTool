import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import time
import io
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click on the left floor view to add a leak point. Adjust the scale slider below to zoom the left image for precise clicking.")

# 1. Plant Selection
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# --- 🔍 LEFT IMAGE ZOOM WORKSPACE ---
st.write("---")
col_zoom1, col_zoom2 = st.columns([2, 3])
with col_zoom1:
    st.markdown("### 🔍 Precise Zoom Workspace Adjuster (Left Only)")
    st.caption("Slide to expand the Left Floor Map image for pixel-perfect targeting.")
with col_zoom2:
    # This adjusts how large the component renders on screen without changing original coordinates
    LEFT_ZOOM_WIDTH = st.slider(
        "Floor Map Zoom Scale (Pixels Wide):", 
        min_value=400, 
        max_value=1400, 
        value=600, 
        step=50
    )
st.write("---")

# Image pathways (Desk on left, Ceiling on right)
if plant == "Plant 1":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
elif plant == "Plant 2":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
else:
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"

# 2. Safely Load and Resize Images to a stable baseline size (e.g. 600px wide)
try:
    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    # We use a solid baseline size for drawing logic so everything scales perfectly
    BASELINE_WIDTH = 600
    
    ratio_left = BASELINE_WIDTH / left_img.width
    height_left = int(left_img.height * ratio_left)
    left_resized = left_img.resize((BASELINE_WIDTH, height_left))
    
    ratio_right = BASELINE_WIDTH / right_img.width
    height_right = int(right_img.height * ratio_right)
    right_resized = right_img.resize((BASELINE_WIDTH, height_right))

except FileNotFoundError:
    st.error("⚠️ Could not find the image files. Please ensure 'Office Ceiling (Roof).jpg' and 'Desk (under roof).jpg' exist inside the 'data/' folder.")
    st.stop()

# Initialize session state tracking list for the active plant
if f"leak_points_{plant}" not in st.session_state:
    st.session_state[f"leak_points_{plant}"] = []

# Persistent counter ensures leak numbers never repeat or shift down on deletion
if f"point_counter_{plant}" not in st.session_state:
    st.session_state[f"point_counter_{plant}"] = 1

# Keep track of the temporary last click to catch new interactions
if f"last_click_{plant}" not in st.session_state:
    st.session_state[f"last_click_{plant}"] = None

# 3. Prepare Image Overlays (Draw all currently active points)
left_display = left_resized.copy()
right_display = right_resized.copy()

draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

# Draw all existing saved points onto both images
for pt in st.session_state[f"leak_points_{plant}"]:
    x, y = pt['x'], pt['y']
    custom_name = pt['name']
    
    # Left View Indicators (Solid Red Dots mapped to custom text name)
    draw_left.ellipse((x - 6, y - 6, x + 6, y + 6), fill="red")
    draw_left.text((x + 8, y - 6), custom_name, fill="yellow")
    
    # Right View Indicators (Cyan Target Rings mapped to identical custom text name)
    draw_right.ellipse((x - 12, y - 12, x + 12, y + 12), outline="cyan", width=3)
    draw_right.ellipse((x - 3, y - 3, x + 3, y + 3), fill="red")
    draw_right.text((x + 14, y - 12), custom_name, fill="cyan")

# 4. Display Side-by-Side Views
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Floor Map View (Click Here)")
    # Passing the width property here allows visual zooming while coordinates stay fixed to baseline dimensions
    clicked_coords = streamlit_image_coordinates(
        left_display,
        width=LEFT_ZOOM_WIDTH,
        key=f"image_click_{plant}"
