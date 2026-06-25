import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import time
import io
import datetime
import requests
import base64

# ------------------------------------------------------------------
# CONFIGURATION: Your live Power Automate URL is embedded here
# ------------------------------------------------------------------
POWER_AUTOMATE_URL = "https://default9b2f9cbe865b4df8a5848494d8c1ef.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/47ed5cfbda7d44a3a9ca56f439adaac0/triggers/manual/paths/invoke?api-version=1"

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Master Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Master Tracking System")
st.info("💡 Drop points to log leaks. Clicking 'Synchronize' will push the data rows AND send a consolidated master overview map showing every dot to your SharePoint dashboard sheet.")

# 1. Plant Selection
plant = st.selectbox("Select Plant:", ['Cambridge - 07', 'Oshawa - 04', 'Windsor - 02'])
plant_key = plant.replace(' ', '_').replace('-', '_')

# Persistent storage setup for historical context tracking across the runtime session
if "master_history_database" not in st.session_state:
    st.session_state["master_history_database"] = {
        'Cambridge___07': [],
        'Oshawa___04': [],
        'Windsor___02': []
    }

# Weather Engine Functionality (Restored to original params setup)
@st.cache_data(ttl=3600)
def get_real_weather_data(plant_name, target_date):
    coordinates = {
        'Cambridge - 07': {"lat": 43.403449, "lon": -80.322832},
        'Oshawa - 04': {"lat": 43.876437, "lon": -78.848991},
        'Windsor - 02': {"lat": 42.286758, "lon": -83.016596}
    }
    
    loc = coordinates.get(plant_name, coordinates['Cambridge - 07'])
    date_str = target_date.strftime("%Y-%m-%d")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": loc["lat"],
        "longitude": loc["lon"],
        "start_date": date_str,
        "end_date": date_str,
        "daily": ["precipitation_sum"],
        "timezone": "America/New_York"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "daily" in data:
                precip_sum = data["daily"]["precipitation_sum"][0]
                return f"{round(precip_sum, 1)} mm" if precip_sum is not None else "0.0 mm"
    except:
        pass
        
    return "0.0 mm"

# Load base image layouts safely using your precise file-naming patterns
try:
    if plant == "Cambridge - 07":
        left_path = "data/CambridgeCAD.png"
        right_path = "data/Cambridge.png"
    elif plant == "Oshawa - 04":
        left_path = "data/OshawaCAD.png"
        right_path = "data/Oshawa.png"
    else:
        left_path = "data/WindsorCAD.png"
        right_path = "data/Windsor.png"

    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    DISPLAY_WIDTH = 600
    left_resized = left_img.resize((DISPLAY_WIDTH, int(left_img.height * (DISPLAY_WIDTH / left_img.width))))
    right_resized = right_img.resize((DISPLAY_WIDTH, int(right_img.height * (DISPLAY_WIDTH / right_img.width))))
except Exception as e:
    st.error(f"⚠️ Base asset assets missing inside data/ directory. Error: {e}")
    st.stop()

# Generate Live Visualizations overlaying ALL historical array coordinates
left_display = left_resized.copy()
right_display = right_resized.copy()
draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

for pt in st.session_state["master_history_database"].get(plant_key, []):
    x, y = pt['x'], pt['y']
    custom_name = pt['name']
    
    # Draw on Floor Plan CAD
    draw_left.ellipse((x-6, y-6, x+6, y+6), fill="red")
    text_pos_left = (x + 10, y - 6)
    bbox_left = draw_left.textbbox(text_pos_left, custom_name)
    padded_bbox_left = (bbox_left[0] - 4, bbox_left[1] - 2, bbox_left[2] + 4, bbox_left[3] + 2)
    draw_left.rectangle(padded_bbox_left, fill="white", outline="red", width=1)
    draw_left.text(text_pos_left, custom_name, fill="red")
    
    # Draw on Satellite Roof Map
    draw_right.ellipse((x-12, y-12, x+12, y+12), outline="cyan", width=3)
    draw_right.ellipse((x-3, y-3, x+3, y+3), fill="red")
    text_pos_right = (x + 16, y - 8)
    bbox_right = draw_right
