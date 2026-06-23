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
st.write("Adjust the left image size independently to pinpoint precise locations. The right view will automatically project the coordinates onto a stable viewport.")

# 1. Plant Selection
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# --- 🔍 LEFT IMAGE ONLY ZOOM CONTROL ---
st.write("---")
col_zoom1, col_zoom2 = st.columns([2, 3])
with col_zoom1:
    st.markdown("### 🔍 Precise Zoom Workspace Adjuster (Left Only)")
    st.caption("Slide to expand the Left Floor Map up to 1400px wide for pixel-perfect accuracy.")
with col_zoom2:
    # This slider will dynamically control the left image size completely independently
    LEFT_DISPLAY_WIDTH = st.slider(
        "Floor Map Scale (Pixels Wide):", 
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

# 2. Safely Load and Resize Images
try:
    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    # 1. Calculate dynamic resizing for the LEFT image based on the ZOOM slider
    ratio_left = LEFT_DISPLAY_WIDTH / left_img.width
    height_left = int(left_img.height * ratio_left)
    left_resized = left_img.resize((LEFT_DISPLAY_WIDTH, height_left))
    
    # 2. Keep the RIGHT target view locked at a comfortable static size (e.g., 600px)
    RIGHT_STATIC_WIDTH = 600
    ratio_right = RIGHT_STATIC_WIDTH / right_img.width
    height_right = int(right_img.height * ratio_right)
    right_resized = right_img.resize((RIGHT_STATIC_WIDTH, height_right))

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

# Draw all existing saved points onto both images using their custom text names
for pt in st.session_state[f"leak_points_{plant}"]:
    # Coordinates are stored relative to the zoom ratio used when they were clicked
    # We must mathematically translate them to match the active, dynamic view configurations
    click_ratio_left = pt
