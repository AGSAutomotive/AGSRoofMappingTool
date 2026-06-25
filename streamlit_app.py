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

# Create a clean key for session state dictionaries
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

# Load base image layouts safely matching your exact file assets
try:
    if "Cambridge" in plant:
        left_path = "data/CambridgeCAD.png"
        right_path = "data/Cambridge.png"
    elif "Oshawa" in plant:
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
    st.error(f"⚠️ Base asset missing inside data/ directory. Error details: {e}")
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
            'id': str(time.time()).replace(".", ""),
            'serial': serial, 
            'x': click['x'], 
            'y': click['y'],
            'name': f"Leak Point {serial}", 
            'start_date': datetime.date.today()
        }
        st.session_state["master_history_database"][plant_key].append(new_point)
        st.rerun()
with c2:
    st.subheader("🦅 Combined Historical Roof View")
    st.image(right_display)

# --- 📋 TRACKING DASHBOARD ---
st.write("---")
st.subheader("📋 Saved Leak Records Dashboard")

points_list = st.session_state["master_history_database"].get(plant_key, [])

if not points_list:
    st.info(f"💡 No leaks mapped yet for {plant}. Click on the left Floor Map image to begin pinning locations.")
else:
    st.info("💡 **Click to rename:** Click directly inside any text box below to customize labels and select dates.")
    
    grid_header1, grid_header2, grid_header3, grid_header4, grid_header5, grid_header6 = st.columns([1.0, 2.2, 1.8, 2.3, 2.3, 1.4])
    with grid_header3:
        st.markdown("**📅 Date Noticed**")
    with grid_header4:
        st.markdown("**🌦️ Precipitation (Day Noticed)**")
    with grid_header5:
        st.markdown("**🌦️ Precipitation (Day Before)**")

    for index, point in enumerate(points_list):
        edit_col1, edit_col2, edit_col3, edit_col4, edit_col5, edit_col6 = st.columns([1.0, 2.2, 1.8, 2.3, 2.3, 1.4])
        
        with edit_col1:
            st.write(f"**#{point['serial']}**")
            
        with edit_col2:
            new_name = st.text_input(
                "Rename label:", 
                value=point['name'], 
                key=f"rename_{plant_key}_{point['id']}",
                label_visibility="collapsed"
            )
            if new_name != point['name']:
                st.session_state["master_history_database"][plant_key][index]['name'] = new_name
                st.rerun()
                
        with edit_col3:
            chosen_date = st.date_input(
                "Date Leak Noticed",
                value=point.get('start_date', datetime.date.today()),
                max_value=datetime.date.today(),
                key=f"date_{plant_key}_{point['id']}",
                label_visibility="collapsed"
            )
            if chosen_date != point.get('start_date'):
                st.session_state["master_history_database"][plant_key][index]['start_date'] = chosen_date
                st.rerun()
        
        day_before_date = chosen_date - datetime.timedelta(days=1)
        
        with edit_col4:
            p_noticed = get_real_weather_data(plant, chosen_date)
            st.markdown(f"**{p_noticed}**")
            
        with edit_col5:
            p_before = get_real_weather_data(plant, day_before_date)
            st.markdown(f"**{p_before}**")
                
        with edit_col6:
            if st.button("🗑️ Delete", key=f"del_{plant_key}_{point['id']}", use_container_width=True):
                st.session_state["master_history_database"][plant_key].pop(index)
                st.rerun()

# --- 🚀 SUBMIT TO SHAREPOINT BLOCK ---
if points_list:
    st.write("---")
    if st.button("🚀 Synchronize Master System Logs & Update SharePoint Images", type="primary", use_container_width=True):
        with st.spinner("Processing composite canvas layouts and updating cloud datasets..."):
            # 1. Compress and encode the entire marked roof overview image containing ALL dots into Base64
            buffer = io.BytesIO()
            right_display.save(buffer, format="JPEG", quality=85)
            base64_string = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Assign landing coordinates on your spreadsheet dashboard depending on the active plant matrix
            grid_positions = {'Cambridge___07': "A2", 'Oshawa___04': "I2", 'Windsor___02': "Q2"}
            target_cell = grid_positions.get(plant_key, "A2")
            
            # 2. Sequential transmission loop
            for pt in points_list:
                chosen_date = pt.get('start_date', datetime.date.today())
                p_not = get_real_weather_data(plant, chosen_date)
                p_bef = get_real_weather_data(plant, chosen_date - datetime.timedelta(days=1))
                
                payload = {
                    "Plant": plant,
                    "Serial": int(pt['serial']),
                    "Label": pt['name'],
                    "DateNoticed": chosen_date.strftime("%Y-%m-%d"),
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
