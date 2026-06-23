import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click anywhere on the map on the left. The corresponding location will automatically calculate and display on the right.")

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
    
    # Standardize widths so the coordinates translate perfectly 1:1
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

# 3. Create Side-by-Side UI
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️Floor Map (Click Here)")
    
    # This modern component simply displays the image and listens for a click
    clicked_coords = streamlit_image_coordinates(
        left_resized,
        key=f"image_click_{plant}" # Unique key per plant
    )

with col2:
    st.subheader("🦅Corresponding Roof View")
    
    # If the user has clicked the image, 'clicked_coords' will contain the X and Y
    if clicked_coords is not None:
        x_click = clicked_coords['x']
        y_click = clicked_coords['y']
        
        # Create a copy of the right image to draw the target on
        right_output = right_resized.copy()
        draw = ImageDraw.Draw(right_output)
        
        # Draw a bright cyan crosshair/circle highlighting the matching leak spot
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
        
        # Display the result using standard Streamlit
        st.image(right_output, use_container_width=False)
        st.success(f"📍 Mapped Coordinates: X={int(x_click)}, Y={int(y_click)}")
    else:
        # What shows up before they click anything
        st.image(right_resized, use_container_width=False)
        st.info("💡 Click a location on the Left Image to map its position.")
