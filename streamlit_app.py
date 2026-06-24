import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import time
import io
import datetime
import requests
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click on the left floor view to add a leak point. Use the dashboard below to manage labels, review multi-day storm profiles, and export to Excel.")

# 1. Plant Selection with your specific names
plant = st.selectbox("Select Manufacturing Plant:", ['Cambridge - 07', 'Oshawa - 04', 'Windsor - 02'])

# --- 🌤️ LIVE OPEN-METEO WEATHER ENGINE ---
@st.cache_data(ttl=3600)  # Cache queries to avoid redundant API hits
def get_real_weather_data(plant_name, target_date):
    """
    Queries Open-Meteo's Archive API using the exact user-provided coordinates
    to extract actual measured Temperature Mean and Total Daily Precipitation.
    """
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
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "timezone": "America/New_York"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "daily" in data:
                temp_mean = data["daily"]["temperature_2m_mean"][0]
                precip_sum = data["daily"]["precipitation_sum"][0]
                
                t_out = f"{round(temp_mean, 1)}°C" if temp_mean is not None else "N/A"
                p_out = f"{round(precip_sum, 1)} mm" if precip_sum is not None else "0.0 mm"
                return t_out, p_out
    except Exception:
        pass
        
    return "N/A", "N/A"


# Image pathways
if plant == "Cambridge - 07":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
elif plant == "Oshawa - 04":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
else:
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"

# 2. Load and Resize Images to a stable layout width (600px)
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
    st.error("⚠️ Could not find the image files. Please ensure files exist inside the 'data/' folder.")
    st.stop()

# Initialize session state tracking list for the active plant
plant_key = plant.replace(' ', '_').replace('-', '_')

if f"leak_points_{plant_key}" not in st.session_state:
    st.session_state[f"leak_points_{plant_key}"] = []

if f"point_counter_{plant_key}" not in st.session_state:
    st.session_state[f"point_counter_{plant_key}"] = 1

if f"last_click_{plant_key}" not in st.session_state:
    st.session_state[f"last_click_{plant_key}"] = None

# 3. Prepare Image Overlays
left_display = left_resized.copy()
right_display = right_resized.copy()

draw_left = ImageDraw.Draw(left_display)
draw_right =
