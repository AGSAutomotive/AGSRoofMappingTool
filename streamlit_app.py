import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import time
import io
import datetime
from zoneinfo import ZoneInfo  # For accurate Eastern Time Zone tracking
import requests
import base64
import threading
import pandas as pd


# ------------------------------------------------------------------
# 🔗 CONFIGURATION: Power Automate Endpoints
# ------------------------------------------------------------------
POWER_AUTOMATE_URL = "https://default9b2f9cbe865b4df8a5848494d8c1ef.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/47ed5cfbda7d44a3a9ca56f439adaac0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=QbnMaks1c-bPXRhe7oHTfnKKO_6PdN48H5AvoV1qdYU"
EXCEL_FETCH_URL = "https://default9b2f9cbe865b4df8a5848494d8c1ef.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/1cada14a49c94756afd2dfa3079ce584/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=eRGiFPth2frXt9B3k9PNGkmSFyf45-bq7fAw-6AniZc" 

st.set_page_config(page_title="AGS Roof Leak Master Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Tracking Tool")
st.info("💡Select plant from the dropdown and enter your AGS email. Then click anywhere on the **floor map** image to plot a leak. Scroll down to to edit more details and submit a report.")

# 1. User & Plant Info Inputs
col_p1, col_p2 = st.columns([4.0, 6.0])
with col_p1:
    plant = st.selectbox("Select Plant:", ['Cambridge - 07', 'Oshawa - 04', 'Sterling South', 'Windsor - 02'])
    plant_key = plant.replace(' ', '_').replace('-', '_')
    
    # Keeps the quick enlargement option check box
    enlarge_map = st.checkbox("🔍 Enlarge Map View (For Detailed Plotting)")
    
with col_p2:
    user_email = st.text_input("📋 Enter your AGS Automotive Email:", placeholder="username@agsautomotive.com").strip().lower()

is_email_valid = user_email.endswith("@agsautomotive.com") and len(user_email) > 18

if "new_pins_batch" not in st.session_state or st.session_state.get("current_active_plant") != plant:
    st.session_state["current_active_plant"] = plant
    st.session_state["new_pins_batch"] = []

# Weather Engine Functionality
@st.cache_data(ttl=3600)
def get_real_weather_data(plant_name, target_date):
    coordinates = {
        'Cambridge - 07': {"lat": 43.403449, "lon": -80.322832},
        'Oshawa - 04': {"lat": 43.876437, "lon": -78.848991},
        'Sterling South': {"lat": 42.542228, "lon": -83.041669},
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
    elif "Sterling" in plant:
        left_path, right_path = "data/SterlingSouthCAD.png", "data/SterlingSouth.png"
    else:
        left_path, right_path = "data/WindsorCAD.png", "data/Windsor.png"

    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    # --- ADDED: Granular Layout Width Slider Bar ---
    # Sets default canvas scaling bounds depending on if the checkbox is checked or unchecked
    min_w = 950 if enlarge_map else 600
    max_w = 1800 if enlarge_map else 1200
    start_w = 1200 if enlarge_map else 800
    
    st.write("")  # Tight layout padding buffer
    map_scale_slider = st.slider(
        "↔️ Adjust Image Display Width Scale (Pixels):", 
        min_value=min_w, 
        max_value=max_w, 
        value=start_w, 
        step=50,
        key=f"slider_{plant_key}"
    )
    DISPLAY_WIDTH = map_scale_slider
    # --------------------------------------------
    
    left_resized = left_img.resize((DISPLAY_WIDTH, int(left_img.height * (DISPLAY_WIDTH / left_img.width))))
    right_resized = right_img.resize((DISPLAY_WIDTH, int(right_img.height * (DISPLAY_WIDTH / right_img.width))))
except Exception as e:
    st.error(f"⚠️ Base asset missing inside data/ directory: {e}")
    st.stop()

left_display = left_resized.copy()
right_display = right_resized.copy()
draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

# Create Transparent overlay layer 
excel_overlay_canvas = Image.new("RGBA", right_resized.size, (255, 255, 255, 0))
draw_excel = ImageDraw.Draw(excel_overlay_canvas)

# Loop and plot through all active session pins directly
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

    # Draw onto transparent overlay layer
    draw_excel.ellipse((x-12, y-12, x+12, y+12), outline="cyan", width=3)
    draw_excel.ellipse((x-3, y-3, x+3, y+3), fill="red")
    draw_excel.rectangle((bbox_right[0]-4, bbox_right[1]-2, bbox_right[2]+4, bbox_right[3]+2), fill="#1A1A1A", outline="cyan", width=1)
    draw_excel.text(text_pos_right, custom_name, fill="cyan")

# --- UPDATED: Vertically Stacked Canvas Layout View ---
st.write("---")

st.subheader("🗺️ Floor Map")
click = streamlit_image_coordinates(left_display, key=f"click_{plant_key}")
if click and click != st.session_state.get(f"lclick_{plant_key}"):
    st.session_state[f"lclick_{plant_key}"] = click
    next_serial = len(st.session_state["new_pins_batch"]) + 1
    
    st.session_state["new_pins_batch"].append({
        'id': str(time.time()).replace(".", ""), 
        'serial': next_serial, 'x': click['x'], 'y': click['y'],
        'name': f"Leak Point {next_serial}", 'start_date': datetime.date.today(),
        'comments': ""
    })
    st.rerun()

st.write("---")
st.subheader("🦅 Roof View")
st.image(right_display)
# -----------------------------------------------------

# --- Grid Form Layout Area ---
st.write("---")
st.subheader("📋 New Unreported Leaks")

if not st.session_state["new_pins_batch"]:
    st.info("💡No new leaks plotted yet for this plant. Click on the floor map image above to plot new leaks.")
else:
    st.info("💡**Click to rename or add details:** Customize the leak label, date, or add important comments below.")
    
    # Adjusted column ratios to comfortably fit a Comments text box
    grid_header1, grid_header2, grid_header3, grid_header4, grid_header5, grid_header6, grid_header7 = st.columns([0.8, 1.8, 1.4, 1.8, 1.8, 2.2, 1.2])
    with grid_header3: st.markdown("**📅 Date Noticed**")
    with grid_header4: st.markdown("**🌦️ Precipitation (Day Noticed)**")
    with grid_header5: st.markdown("**🌦️ Precipitation (Day Before)**")
    with grid_header6: st.markdown("**💬 Important Comments / Notes**")

    for index, point in enumerate(st.session_state["new_pins_batch"]):
        if 'comments' not in point:
            st.session_state["new_pins_batch"][index]['comments'] = ""
            
        c_idx, c_lbl, c_dt, c_w1, c_w2, c_cmt, c_del = st.columns([0.8, 1.8, 1.4, 1.8, 1.8, 2.2, 1.2])
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
        
        # Live Comments Input Box
        with c_cmt:
            new_comment = st.text_input("Comments:", value=point['comments'], placeholder="e.g., Near stamping press, pooling", key=f"cmt_{point['id']}", label_visibility="collapsed")
            if new_comment != point['comments']:
                st.session_state["new_pins_batch"][index]['comments'] = new_comment
                st.rerun()
        
        with c_del:
            if st.button("🗑️ Remove", key=f"del_{point['id']}", use_container_width=True):
                st.session_state["new_pins_batch"].pop(index)
                st.rerun()

# --- 🚀 BATCHED SUBMIT ENGINE TRANSMISSION BLOCK ---
if st.session_state["new_pins_batch"]:
    st.write("---")
    
    if not is_email_valid:
        st.error("🛑 **Submission Locked:** You must enter a valid AGS Automotive email address above (`@agsautomotive.com`) before you can submit this leak report.")
    else:
        st.info("💡Once all new leaks are plotted, click **'Report Leaks'** button below to save.")
    
    st.markdown("""
        <style>
            div[data-testid="stButton"] button[kind="primary"] p {
                font-size: 24px !important;
                font-weight: bold !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    btn_layout_col, spacer_col = st.columns([2.5, 7.5])
    
    with btn_layout_col:
        if st.button("🚀 Report Leaks", type="primary", use_container_width=True, disabled=not is_email_valid):
            with st
