import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import time
import io
import datetime
import requests
import base64

# ------------------------------------------------------------------
# CONFIGURATION: Your authenticated live Power Automate URL
# ------------------------------------------------------------------
POWER_AUTOMATE_URL = "https://default9b2f9cbe865b4df8a5848494d8c1ef.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/47ed5cfbda7d44a3a9ca56f439adaac0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=QbnMaks1c-bPXRhe7oHTfnKKO_6PdN48H5AvoV1qdYU"

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Master Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Master Tracking System")

# 1. Plant Selection
plant = st.selectbox("Select Plant:", ['Cambridge - 07', 'Oshawa - 04', 'Windsor - 02'])
plant_key = plant.replace(' ', '_').replace('-', '_')

# Clean local session tracking state (wipes when page reloads)
if "new_pins_batch" not in st.session_state or st.session_state.get("current_active_plant") != plant:
    st.session_state["current_active_plant"] = plant
    st.session_state["new_pins_batch"] = []

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
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": loc["lat"], "longitude": loc["lon"],
        "start_date": date_str, "end_date": date_str,
        "daily": ["precipitation_sum"], "timezone": "America/New_York"
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            p_sum = res.json()["daily"]["precipitation_sum"][0]
            return f"{round(p_sum, 1)} mm" if p_sum is not None else "0.0 mm"
    except: pass
    return "0.0 mm"

# Load base image layouts safely
try:
    if "Cambridge" in plant:
        left_path, right_path = "data/CambridgeCAD.png", "data/Cambridge.png"
    elif "Oshawa" in plant:
        left_path, right_path = "data/OshawaCAD.png", "data/Oshawa.png"
    else:
        left_path, right_path = "data/WindsorCAD.png", "data/Windsor.png"

    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    DISPLAY_WIDTH = 600
    left_resized = left_img.resize((DISPLAY_WIDTH, int(left_img.height * (DISPLAY_WIDTH / left_img.width))))
    right_resized = right_img.resize((DISPLAY_WIDTH, int(right_img.height * (DISPLAY_WIDTH / right_img.width))))
except Exception as e:
    st.error(f"⚠️ Base asset missing inside data/ directory: {e}")
    st.stop()

# Build app display canvases
left_display = left_resized.copy()
right_display = right_resized.copy()
draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

# 🧠 CRITICAL CHANGE: Create a completely BLANK, TRANSPARENT overlay canvas for Excel
# This allows pins to stack incrementally in Excel without hiding previous sync actions
excel_overlay_canvas = Image.new("RGBA", right_resized.size, (255, 255, 255, 0))
draw_excel = ImageDraw.Draw(excel_overlay_canvas)

# Loop ONLY through the new unsynced points dropped in this specific session
for pt in st.session_state["new_pins_batch"]:
    x, y, custom_name = pt['x'], pt['y'], pt['name']
    
    # Draw on local App CAD View
    draw_left.ellipse((x-6, y-6, x+6, y+6), fill="red")
    text_pos_left = (x + 10, y - 6)
    bbox_left = draw_left.textbbox(text_pos_left, custom_name)
    draw_left.rectangle((bbox_left[0]-4, bbox_left[1]-2, bbox_left[2]+4, bbox_left[3]+2), fill="white", outline="red", width=1)
    draw_left.text(text_pos_left, custom_name, fill="red")
    
    # Draw on local App Satellite Roof View
    draw_right.ellipse((x-12, y-12, x+12, y+12), outline="cyan", width=3)
    draw_right.ellipse((x-3, y-3, x+3, y+3), fill="red")
    text_pos_right = (x + 16, y - 8)
    bbox_right = draw_right.textbbox(text_pos_right, custom_name)
    draw_right.rectangle((bbox_right[0]-4, bbox_right[1]-2, bbox_right[2]+4, bbox_right[3]+2), fill="#1A1A1A", outline="cyan", width=1)
    draw_right.text(text_pos_right, custom_name, fill="cyan")

    # Draw onto the transparent Excel layout layer
    draw_excel.ellipse((x-12, y-12, x+12, y+12), outline="cyan", width=3)
    draw_excel.ellipse((x-3, y-3, x+3, y+3), fill="red")
    draw_excel.rectangle((bbox_right[0]-4, bbox_right[1]-2, bbox_right[2]+4, bbox_right[3]+2), fill="#1A1A1A", outline="cyan", width=1)
    draw_excel.text(text_pos_right, custom_name, fill="cyan")

# Display Side-by-Side Images
st.write("---")
col1, col2 = st.columns(2)
with col1:
    st.subheader("🗺️ Floor Map View")
    click = streamlit_image_coordinates(left_display, key=f"click_{plant_key}")
    if click and click != st.session_state.get(f"lclick_{plant_key}"):
        st.session_state[f"lclick_{plant_key}"] = click
        next_serial = len(st.session_state["new_pins_batch"]) + 1
        
        st.session_state["new_pins_batch"].append({
            'id': str(time.time()).replace(".", ""),
            'serial': next_serial, 'x': click['x'], 'y': click['y'],
            'name': f"Leak Point {next_serial}", 'start_date': datetime.date.today()
        })
        st.rerun()
with col2:
    st.subheader("🦅 Current Staged Session View")
    st.image(right_display)

# --- Grid Form Layout Area ---
st.write("---")
st.subheader("📋 New Unsynced Leak Records Queue")

if not st.session_state["new_pins_batch"]:
    st.info("💡 No new pins staged in current session. Click on the left image to plot new leak coordinates.")
else:
    for index, point in enumerate(st.session_state["new_pins_batch"]):
        c_idx, c_lbl, c_dt, c_w1, c_w2, c_del = st.columns([1.0, 2.2, 1.8, 2.3, 2.3, 1.4])
        with c_idx: st.write(f"**#{point['serial']}**")
        with c_lbl:
            new_name = st.text_input("Rename:", value=point['name'], key=f"ren_{point['id']}", label_visibility="collapsed")
            if new_name != point['name']:
                st.session_state["new_pins_batch"][index]['name'] = new_name
                st.rerun()
        with c_dt:
            chosen_date = st.date_input("Date:", value=point['start_date'], max_value=datetime.date.today(), key=f"dt_{point['id']}", label_visibility="collapsed")
            if chosen_date != point['start_date']:
                st.session_state["new_pins_batch"][index]['start_date'] = chosen_date
                st.rerun()
                
        with c_w1: st.markdown(f"**{get_real_weather_data(plant, chosen_date)}**")
        with c_w2: st.markdown(f"**{get_real_weather_data(plant, chosen_date - datetime.timedelta(days=1))}**")
        with c_del:
            if st.button("🗑️ Remove", key=f"del_{point['id']}", use_container_width=True):
                st.session_state["new_pins_batch"].pop(index)
                st.rerun()

# --- 🚀 SUBMIT ENGINE TRANSMISSION BLOCK ---
if st.session_state["new_pins_batch"]:
    st.write("---")
    if st.button("🚀 Synchronize Master System Logs & Update SharePoint Images", type="primary", use_container_width=True):
        with st.spinner("Uploading and updating consolidated overview maps..."):
            # Compress and encode the transparent overlay matrix into Png format (to preserve alpha layers)
            buffer = io.BytesIO()
            excel_overlay_canvas.save(buffer, format="PNG")
            base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            grid_positions = {'Cambridge___07': "A2", 'Oshawa___04': "M2", 'Windsor___02': "Y2"}
            target_cell = grid_positions.get(plant_key, "A2")
            
            # Send text rows sequentially
            for pt in st.session_state["new_pins_batch"][:-1]:
                c_date = pt['start_date']
                payload = {
                    "Plant": plant, "Serial": int(pt['serial']), "Label": pt['name'],
                    "DateNoticed": c_date.strftime("%Y-%m-%d"),
                    "PrecipNoticed": get_real_weather_data(plant, c_date),
                    "PrecipBefore": get_real_weather_data(plant, c_date - datetime.timedelta(days=1)),
                    "CoordinateX": int(pt['x']), "CoordinateY": int(pt['y']),
                    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Base64MapData": "", "DashboardCell": target_cell
                }
                requests.post(POWER_AUTOMATE_URL, json=payload)
                time.sleep(1.5)
            
            # Send final payload containing the fresh dots overlay string
            last_pt = st.session_state["new_pins_batch"][-1]
            c_date = last_pt['start_date']
            final_payload = {
                "Plant": plant, "Serial": int(last_pt['serial']), "Label": last_pt['name'],
                "DateNoticed": c_date.strftime("%Y-%m-%d"),
                "PrecipNoticed": get_real_weather_data(plant, c_date),
                "PrecipBefore": get_real_weather_data(plant, c_date - datetime.timedelta(days=1)),
                "CoordinateX": int(last_pt['x']), "CoordinateY": int(last_pt['y']),
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Base64MapData": base64_string, "DashboardCell": target_cell
            }
            requests.post(POWER_AUTOMATE_URL, json=final_payload)
            
            # Wipe local queue so the app returns to a fresh blank slate for the next run
            st.session_state["new_pins_batch"] = []
            st.success("🎉 Sync complete! Transparent pin layer deployed directly to Excel dashboard matrix.")
            time.sleep(1)
            st.rerun()
