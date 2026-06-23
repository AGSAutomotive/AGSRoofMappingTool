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
st.write("Click on the left floor view to add a leak point. Use the dashboard below to manage labels and export everything directly to Excel.")

# 1. Plant Selection
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# --- 🔍 WORKSPACE ZOOM CONTROL ---
st.write("---")
col_zoom1, col_zoom2 = st.columns([2, 3])
with col_zoom1:
    st.markdown("### 🔍 Precise Zoom Workspace Adjuster")
    st.caption("Increase the display width to zoom in on the image and map a highly precise location.")
with col_zoom2:
    # Let the user dynamically adjust the workspace size for clear zoom mapping
    DISPLAY_WIDTH = st.slider(
        "Workspace View Scale (Pixels Wide):", 
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
    
    # Standardize widths based on the active dynamic Zoom selection slider
    ratio_left = DISPLAY_WIDTH / left_img.width
    height_left = int(left_img.height * ratio_left)
    left_resized = left_img.resize((DISPLAY_WIDTH, height_left))
    
    ratio_right = DISPLAY_WIDTH / right_img.width
    height_right = int(right_img.height * ratio_right)
    right_resized = right_img.resize((DISPLAY_WIDTH, height_right))

except FileNotFoundError:
    st.error("⚠️ Could not find the image files. Please ensure 'Office Ceiling (Roof).jpg' and 'Desk (under roof).jpg' exist inside the 'data/' folder.")
    st.stop()

# Initialize session state tracking list for the active plant
if f"leak_points_{plant}" not in st.session_state:
    st.session_state[f"leak_points_{plant}"] = []

# Persistent counter ensures leak numbers never repeat or shift down on deletion
if f"point_counter_{plant}" not in st.session_state:
    st.session_state[f"point_counter_{plant}"] = 1
