import sys
import types
import streamlit as st
import io
import base64
import inspect

# =========================================================================
# HYBRID PATCH: Fixes blank canvas while protecting standard st.image()
# =========================================================================
# Keep a reference to the real original function
try:
    import streamlit.elements.lib.image_utils as image_utils
    ORIG_IMAGE_TO_URL = image_utils.image_to_url
except Exception:
    ORIG_IMAGE_TO_URL = None

def hybrid_image_to_url(data, width=None, clamp=False, channels="RGB", output_format="JPEG", image_id="canvas_img"):
    # Look at the execution stack to see if the canvas component triggered this
    is_canvas = any("streamlit_drawable_canvas" in frame.filename for frame in inspect.stack() if frame.filename)

    if is_canvas:
        # Force Base64 string so Streamlit Cloud iframe cannot block the image
        if hasattr(data, "save"):
            buffered = io.BytesIO()
            data.save(buffered, format="JPEG")
            img_bytes = buffered.getvalue()
        elif isinstance(data, bytes):
            img_bytes = data
        else:
            img_bytes = bytes(data)
            
        b64_str = base64.b64encode(img_bytes).decode()
        return f"data:image/jpeg;base64,{b64_str}"
    
    # If standard st.image() triggered this, fall back to native streamlit behavior safely
    if ORIG_IMAGE_TO_URL is not None:
        return ORIG_IMAGE_TO_URL(data, width, clamp, channels, output_format, image_id)
    return ""

# Apply the patch
try:
    import streamlit.elements.image as st_image
    st_image.image_to_url = hybrid_image_to_url
except Exception:
    pass

if ORIG_IMAGE_TO_URL is not None:
    image_utils.image_to_url = hybrid_image_to_url
# =========================================================================

from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click anywhere on the map on the left to mark a leak. The corresponding location will automatically calculate and display on the right view.")

# Plant Selection Configuration
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# Swapped paths: Desk is on the left, Ceiling is on the right
if plant == "Plant 1":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
elif plant == "Plant 2":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
else:
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"

# Safely Load and Resize Images
try:
    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    # Fix a display width to prevent any image cutting off or misalignment
    DISPLAY_WIDTH = 600
    
    # Calculate aspect ratio based scaling
    l_width, l_height = left_img.size
    scale_ratio = DISPLAY_WIDTH / float(l_width)
    display_height = int(float(l_height) * float(scale_ratio))
    
    # Resize both for clean parallel canvas layout
    left_resized = left_img.resize((DISPLAY_WIDTH, display_height))
    right_resized = right_img.resize((DISPLAY_WIDTH, display_height))

except FileNotFoundError:
    st.error("⚠️ Could not find the image files in the 'data/' folder. Please ensure 'Office Ceiling (Roof).jpg' and 'Desk (under roof).jpg' exist inside your repository.")
    st.stop()

# Create Side-by-Side App Interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("📸 Primary Map View (Click Here)")
    
    # Interactive clickable canvas layer
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",  # semi-transparent red
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=left_resized,
        update_streamlit=True,
        height=display_height,
        width=DISPLAY_WIDTH,
        drawing_mode="point", # simple dot click mapping
        point_display_radius=6,
        key=f"canvas_fixed_{plant}" 
    )

with col2:
    st.subheader("🦅 Corresponding Target View")
    
    # Process clicks if user registers any coordinates
    if canvas_result.image_data is not None and len(canvas_result.json_data["objects"]) > 0:
        # Pull the absolute last click coordinates made by user
        last_object = canvas_result.json_data["objects"][-1]
        x_click = last_object["left"]
        y_click = last_object["top"]
        
        # Draw a targeting reticle over the right image at identical relative space
        right_output = right_resized.copy()
        draw = ImageDraw.Draw(right_output)
        
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
        
        # Display natively without crashing
        st.image(right_output, use_container_width=True)
        st.success(f"📍 Leak mapped coordinates relative to layout: X={int(x_click)}, Y={int(y_click)}")
    else:
        # Base fallback view before any click triggers
        st.image(right_resized, use_container_width=True)
        st.info("💡 Click a leak location on the Left Image to view its mapped position on the Right.")
