import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click on the left floor view to add a leak point. Manage, rename, or delete your saved points in the dashboard below.")

# 1. Plant Selection
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

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
    
    DISPLAY_WIDTH = 600
    
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

# Keep track of the temporary last click to catch new interactions
if f"last_click_{plant}" not in st.session_state:
    st.session_state[f"last_click_{plant}"] = None

# 3. Prepare Image Overlays (Draw all currently active points)
left_display = left_resized.copy()
right_display = right_resized.copy()

draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

# Draw all existing saved points onto both images
for idx, pt in enumerate(st.session_state[f"leak_points_{plant}"]):
    x, y = pt['x'], pt['y']
    
    # Left View Indicators (Solid Red Dots)
    draw_left.ellipse((x - 6, y - 6, x + 6, y + 6), fill="red")
    draw_left.text((x + 8, y - 6), str(idx + 1), fill="yellow")
    
    # Right View Indicators (Cyan Target Rings)
    draw_right.ellipse((x - 12, y - 12, x + 12, y + 12), outline="cyan", width=3)
    draw_right.ellipse((x - 3, y - 3, x + 3, y + 3), fill="red")
    draw_right.text((x + 14, y - 12), pt['name'], fill="cyan")

# 4. Display Side-by-Side Views
col1, col2 = st.columns(2)

with col1:
    st.subheader("🪵 Floor Map View (Click Here)")
    clicked_coords = streamlit_image_coordinates(
        left_display,
        key=f"image_click_{plant}" 
    )
    
    # Process if a brand new click location is registered
    if clicked_coords is not None and clicked_coords != st.session_state[f"last_click_{plant}"]:
        st.session_state[f"last_click_{plant}"] = clicked_coords
        
        # Add the new coordinates to our tracking list
        new_id = len(st.session_state[f"leak_points_{plant}"]) + 1
        st.session_state[f"leak_points_{plant}"].append({
            'x': clicked_coords['x'],
            'y': clicked_coords['y'],
            'name': f"Leak Point {new_id}"
        })
        st.rerun()

with col2:
    st.subheader("🦅 Corresponding Roof View")
    st.image(right_display, use_container_width=False)

# --- 📋 TRACKING LIST & MANAGEMENT DASHBOARD ---
st.write("---")
st.subheader("📋 Saved Leak Records Dashboard")

points_list = st.session_state[f"leak_points_{plant}"]

if not points_list:
    st.info("💡 No leaks mapped yet. Click on the left Floor Map image to begin pinning locations.")
else:
    # Build control rows for editing items individually
    for index, point in enumerate(points_list):
        # Create a tidy row layout layout for listing properties
        edit_col1, edit_col2, edit_col3 = st.columns([1, 3, 2])
        
        with edit_col1:
            st.write(f"**#{index + 1}** (X: {int(point['x'])}, Y: {int(point['y'])})")
            
        with edit_col2:
            # Inline text input allows real-time renaming updates
            new_name = st.text_input(
                "Rename label:", 
                value=point['name'], 
                key=f"rename_{plant}_{index}",
                label_visibility="collapsed"
            )
            if new_name != point['name']:
                st.session_state[f"leak_points_{plant}"][index]['name'] = new_name
                st.rerun()
                
        with edit_col3:
            # Delete handler removes the item from index list
            if st.button("🗑️ Delete Record", key=f"del_{plant}_{index}"):
                st.session_state[f"leak_points_{plant}"].pop(index)
                st.rerun()
