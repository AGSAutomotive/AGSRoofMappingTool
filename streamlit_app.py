import sys
import types
import streamlit as st

# =========================================================================
# 1. THE ULTIMATE MODERN STREAMLIT COMPATIBILITY PATCH
# =========================================================================
import io
from streamlit.runtime import get_instance
from streamlit.runtime.media_file_manager import MediaFileManager

def ultimate_image_to_url(data, width=None, clamp=False, channels="RGB", output_format="JPEG", image_id="canvas_img"):
    """
    Directly bypasses Streamlit's internal layout checking engine by safely 
    registering the image bytes straight into the modern Streamlit Media Manager.
    """
    # If it's already a PIL image, drop its format down to bytes
    if hasattr(data, "save"):
        buffered = io.BytesIO()
        data.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
    elif isinstance(data, bytes):
        img_bytes = data
    else:
        img_bytes = bytes(data)

    # Secure an active instance of the file manager engine
    runtime_instance = get_instance()
    if runtime_instance is not None:
        file_mgr = runtime_instance.media_file_mgr
        # Directly register raw bytes and return the served web URL route string
        media_file = file_mgr.add(img_bytes, "image/jpeg", image_id)
        return media_file.url
    return ""

# Overwrite the function everywhere Streamlit or Canvas might call it
try:
    import streamlit.elements.image as st_image
    st_image.image_to_url = ultimate_image_to_url
except Exception:
    pass

try:
    import streamlit.elements.lib.image_utils as image_utils
    image_utils.image_to_url = ultimate_image_to_url
except Exception:
    pass
# =========================================================================

from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click anywhere on the map on the left to mark a leak. The corresponding location will automatically calculate and display on the right view.")

# 2. Plant Selection Configuration
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# Image pathways
if plant == "Plant 1":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
elif plant == "Plant 2":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
else:
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"

# 3. Safely Load and Resize Images
try:
    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    DISPLAY_WIDTH = 600
    
    # Calculate uniform dimensions
    l_width, l_height = left_img.size
    scale_ratio = DISPLAY_WIDTH / float(l_width)
    display_height = int(float(l_height) * float(scale_ratio))
    
    left_resized = left_img.resize((DISPLAY_WIDTH, display_height))
    right_resized = right_img.resize((DISPLAY_WIDTH, display_height))

except FileNotFoundError:
    st.error("⚠️ Could not find the image files in the 'data/' folder. Please ensure 'Office Ceiling (Roof).jpg' and 'Desk (under roof).jpg' exist inside your repository.")
    st.stop()

# 4. Create Side-by-Side App Interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("📸 Primary Map View (Click Here)")
    
    # Interactive clickable canvas layer using the safely processed PIL Image
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",  
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=left_resized, 
        update_streamlit=True,
        height=display_height,
        width=DISPLAY_WIDTH,
        drawing_mode="point", 
        point_display_radius=6,
        key=f"canvas_final_{plant}" 
    )

with col2:
    st.subheader("🦅 Corresponding Target View")
    
    # Process clicks if user registers any coordinates
    if canvas_result.image_data is not None and len(canvas_result.json_data["objects"]) > 0:
        last_object = canvas_result.json_data["objects"][-1]
        x_click = last_object["left"]
        y_click = last_object["top"]
        
        right_output = right_resized.copy()
        draw = ImageDraw.Draw(right_output)
        
        # Target ring
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
        
        st.image(right_output, use_container_width=True)
        st.success(f"📍 Leak mapped coordinates relative to layout: X={int(x_click)}, Y={int(y_click)}")
    else:
        st.image(right_resized, use_container_width=True)
        st.info("💡 Click a leak location on the Left Image to view its mapped position on the Right.")
