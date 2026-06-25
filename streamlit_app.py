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

# Weather Engine Functionality
@st.cache_data(ttl=3600)
def get_real_weather_data(plant_name, target_date):
    coordinates = {
        'Cambridge - 07': {"lat": 43.403449, "lon": -80.322832},
        'Oshawa - 04': {"lat": 43.876437, "lon": -78.848991},
        'Windsor - 02': {"lat": 42.286758, "lon": -83.016596}
    }
    loc = coordinates.get(plant_name, coordinates['Cambridge - 07'])
    date_str = target_date.strftime("%Y-%m-%d")
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={loc['lat']}&longitude={loc['lon']}&start_date={date_str}&end_date={date_str}&daily=precipitation_sum&timezone=America/New_York"
    try:
        res = requests.get(url, timeout=5).json()
        precip = res['daily']['precipitation_sum'][0]
        return f"{round(precip, 1)} mm" if precip is not None else "0.0 mm"
    except:
        return "0.0 mm"

# Load base image layouts safely
try:
    # Handle filename cleanups
    clean_key = plant_key.replace("___", "").replace("_", "")
    left_path = f"data/{clean_key}CAD.png"
    right_path = f"data/{clean_key}.png"

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
    bbox_right = draw_right.textbbox(text_pos_right, custom_name)
    padded_bbox_right = (bbox_right[0] - 4, bbox_right[1] - 2, bbox_right[2] + 4, bbox_right[3] + 2)
    draw_right.rectangle(padded_bbox_right, fill="#1A1A1A", outline="cyan", width=1)
    draw_right.text(text_pos_right, custom_name, fill="cyan")

# Render Layout images side-by-side
st.write("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader("🗺️ Floor Map View")
    click = streamlit_image_coordinates(left_display, key=f"click_{plant_key}")
    if click and click != st.session_state.get(f"lclick_{plant_key}"):
        st.session_state[f"lclick_{plant_key}"] = click
        serial = len(st.session_state["master_history_database"][plant_key]) + 1
        
        new_point = {
            'serial': serial, 
            'x': click['x'], 
            'y': click['y'],
            'name': f"Leak Point {serial}", 
            'date': datetime.date.today()
        }
        st.session_state["master_history_database"][plant_key].append(new_point)
        st.rerun()
with c2:
    st.subheader("🦅 Combined Historical Roof View")
    st.image(right_display)

# Dynamic Synchronize Engine Execution Block
st.write("---")
active_points = st.session_state["master_history_database"].get(plant_key, [])

if active_points:
    st.subheader("📝 Process Current Logs")
    
    if st.button("🚀 Synchronize Master System Logs & Update SharePoint Images", type="primary", use_container_width=True):
        if POWER_AUTOMATE_URL == "YOUR_POWER_AUTOMATE_HTTP_URL_HERE":
            st.error("⚠️ Update your target integration API webhook URL link configuration at line 14!")
        else:
            with st.spinner("Processing composite canvas layouts and updating cloud datasets..."):
                # 1. Compress and encode the entire marked roof overview image containing ALL dots into Base64
                buffer = io.BytesIO()
                right_display.save(buffer, format="JPEG", quality=85)
                base64_string = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Assign landing coordinates on your spreadsheet dashboard depending on the active plant matrix
                grid_positions = {'Cambridge___07': "A2", 'Oshawa___04': "I2", 'Windsor___02': "Q2"}
                target_cell = grid_positions.get(plant_key, "A2")
                
                # 2. Sequential transmission loop
                for pt in active_points:
                    p_not = get_real_weather_data(plant, pt['date'])
                    p_bef = get_real_weather_data(plant, pt['date'] - datetime.timedelta(days=1))
                    
                    payload = {
                        "Plant": plant,
                        "Serial": int(pt['serial']),
                        "Label": pt['name'],
                        "DateNoticed": pt['date'].strftime("%Y-%m-%d"),
                        "PrecipNoticed": p_not,
                        "PrecipBefore": p_bef,
                        "CoordinateX": int(pt['x']),
                        "CoordinateY": int(pt['y']),
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Base64MapData": base64_string,
                        "DashboardCell": target_cell
                    }
                    requests.post(POWER_AUTOMATE_URL, json=payload)
                
                st.success("🎉 Master Excel rows logged! Multi-point canvas dashboard refreshed live on SharePoint!")
