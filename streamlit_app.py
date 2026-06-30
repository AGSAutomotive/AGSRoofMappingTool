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
# AUTOMATED KEEP-AWAKE ENGINE (Prevents 12-Hour Idle Sleep)
# ------------------------------------------------------------------
def background_ping_loop(url):
    """Sends a silent web request to the app URL every 30 minutes to reset the sleep clock."""
    time.sleep(30)
    while True:
        try:
            requests.get(url, timeout=10)
        except Exception:
            pass
        time.sleep(1800)

APP_PUBLIC_URL = "https://agsroofmappingtool.streamlit.app/"

if "keep_awake_thread_started" not in st.session_state:
    st.session_state["keep_awake_thread_started"] = True
    bg_thread = threading.Thread(target=background_ping_loop, args=(APP_PUBLIC_URL,), daemon=True)
    bg_thread.start()

# ------------------------------------------------------------------
# 🔗 CONFIGURATION: Power Automate Endpoints
# ------------------------------------------------------------------
POWER_AUTOMATE_URL = "https://default9b2f9cbe865b4df8a5848494d8c1ef.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/47ed5cfbda7d44a3a9ca56f439adaac0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=QbnMaks1c-bPXRhe7oHTfnKKO_6PdN48H5AvoV1qdYU"
EXCEL_FETCH_URL = "https://default9b2f9cbe865b4df8a5848494d8c1ef.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/1cada14a49c94756afd2dfa3079ce584/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=eRGiFPth2frXt9B3k9PNGkmSFyf45-bq7fAw-6AniZc" 

st.set_page_config(page_title="AGS Roof Leak Master Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Tracking Tool")

# 1. User & Plant Info Inputs
col_p1, col_p2 = st.columns([4.0, 6.0])
with col_p1:
    plant = st.selectbox("Select Plant:", ['Cambridge - 07', 'Oshawa - 04', 'Windsor - 02'])
    plant_key = plant.replace(' ', '_').replace('-', '_')
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

# Display Side-by-Side Images
st.write("---")
col1, col2 = st.columns(2)
with col1:
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
with col2:
    st.subheader("🦅 Roof View")
    st.image(right_display)

# --- Grid Form Layout Area ---
st.write("---")
st.subheader("📋 New Unreported Leaks")

if not st.session_state["new_pins_batch"]:
    st.info("💡No new leaks plotted yet for this plant. Click on the left image to plot new leaks.")
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
            with st.spinner("Generating consolidated maps and compiling summary table..."):
                
                final_merged_image = right_resized.convert("RGBA")
                final_merged_image.paste(excel_overlay_canvas, (0, 0), excel_overlay_canvas)
                final_merged_image = final_merged_image.convert("RGB")
                
                buffer = io.BytesIO()
                final_merged_image.save(buffer, format="JPEG", quality=90)
                base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                local_timestamp = datetime.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
                
                grid_positions = {'Cambridge___07': "A2", 'Oshawa___04': "M2", 'Windsor___02': "Y2"}
                target_cell = grid_positions.get(plant_key, "A2")
                
                # Package ALL itemized points together into a structured dynamic data array
                leak_items_list = []
                for pt in st.session_state["new_pins_batch"]:
                    c_date = pt['start_date']
                    leak_items_list.append({
                        "Serial": int(pt['serial']),
                        "Label": pt['name'],
                        "DateNoticed": c_date.strftime("%Y-%m-%d"),
                        "PrecipNoticed": get_real_weather_data(plant, c_date),
                        "PrecipBefore": get_real_weather_data(plant, c_date - datetime.timedelta(days=1)),
                        "CoordinateX": int(pt['x']),
                        "CoordinateY": int(pt['y']),
                        "Comments": pt.get('comments', "").strip()
                    })
                
                # --- GENERATED EMAIL TABLE CONSTRUCT ENGINE ---
                raw_df = pd.DataFrame(leak_items_list)
                
                # Drop structural tracking columns, keeping Comments visible
                email_df = raw_df.drop(columns=["Serial", "CoordinateX", "CoordinateY"], errors="ignore")
                
                # Give columns clean professional formatting headers
                email_df.columns = ["Leak Description", "Date Noticed", "Precipitation (Day)", "Precipitation (Before)", "Comments / Actions Needed"]
                
                html_table_body = email_df.to_html(index=False, classes="clean-notification-table", escape=False)
                
                styled_email_table = f"""
                <style>
                    .clean-notification-table {{
                        border-collapse: collapse;
                        width: 100%;
                        font-family: Calibri, Arial, sans-serif;
                        font-size: 14px;
                        margin: 16px 0;
                    }}
                    .clean-notification-table th {{
                        background-color: #003366;
                        color: #ffffff;
                        font-weight: bold;
                        text-align: left;
                        padding: 12px 24px;
                        border: 1px solid #002244;
                        min-width: 140px;
                    }}
                    .clean-notification-table td {{
                        padding: 10px 24px;
                        border: 1px solid #dddddd;
                        text-align: left;
                        vertical-align: middle;
                    }}
                    .clean-notification-table tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                </style>
                {html_table_body}
                """
                
                master_payload = {
                    "Plant": plant,
                    "Timestamp": local_timestamp,
                    "ReporterEmail": user_email,
                    "DashboardCell": target_cell,
                    "Base64MapData": base64_string,
                    "LeaksArray": leak_items_list,       
                    "EmailTableHTML": styled_email_table 
                }
                
                requests.post(POWER_AUTOMATE_URL, json=master_payload)
                
                st.session_state["new_pins_batch"] = []
                st.success("🎉 All leaks successfully reported!")
                time.sleep(1)
                st.rerun()

# ------------------------------------------------------------------
# 🔒 DYNAMIC HISTORICAL MAP ENGINE (Renders at Very Bottom)
# ------------------------------------------------------------------
st.write("---")
with st.expander("🔒 Administrator History View (Live Database Sync)", expanded=False):
    st.subheader(f"📊 Historical Leak Map — {plant}")
    
    historical_records = []
    try:
        response = requests.get(f"{EXCEL_FETCH_URL}&cb={time.time()}", timeout=8)
        if response.status_code == 200:
            historical_records = response.json()
            if not isinstance(historical_records, list):
                historical_records = response.json().get("value", [])
    except Exception as e:
        st.error("⚠️ Failed to communicate with live Power Automate database retriever flow.")

    plant_historical_records = []
    for r in historical_records:
        if str(r.get("Plant", "")).strip() == plant:
            raw_date = r.get("DateNoticed", "")
            try:
                if str(raw_date).isdigit() or isinstance(raw_date, (int, float)):
                    serial_num = int(float(raw_date))
                    converted_dt = datetime.date(1899, 12, 30) + datetime.timedelta(days=serial_num)
                    r["DateNoticed"] = converted_dt.strftime("%Y/%m/%d")
            except Exception:
                pass
            plant_historical_records.append(r)

    if not plant_historical_records:
        st.info("🍃 The historical database is currently empty.")
    else:
        st.caption(f"Showing {len(plant_historical_records)} historical leak points.")
        
        history_canvas = right_resized.copy()
        draw_history = ImageDraw.Draw(history_canvas)
        
        for record in plant_historical_records:
            try:
                hx = int(float(record["CoordinateX"]))
                hy = int(float(record["CoordinateY"]))
                h_label = str(record.get("Label", "Unlabeled Point"))
                
                draw_history.ellipse((hx-10, hy-10, hx+10, hy+10), outline="yellow", width=2)
                draw_history.ellipse((hx-3, hy-3, hx+3, hy+3), fill="orange")
                
                h_text_pos = (hx + 14, hy - 6)
                h_bbox = draw_history.textbbox(h_text_pos, h_label)
                draw_history.rectangle((h_bbox[0]-3, h_bbox[1]-1, h_bbox[2]+3, h_bbox[3]+1), fill="#262730")
                draw_history.text(h_text_pos, h_label, fill="yellow")
            except:
                pass 
            
        hist_col1, hist_col2 = st.columns([6.0, 4.0])
        with hist_col1:
            st.image(history_canvas, use_container_width=False, caption="Live Cumulative Database History View")
        with hist_col2:
            try:
                # Transformed historical dataframe to hide 'Serial' and display 'Comments'
                df_view = pd.DataFrame(plant_historical_records)
                
                # Handle cases where the spreadsheet doesn't have a record yet safely
                if "Comments" not in df_view.columns:
                    df_view["Comments"] = ""
                
                # Explicitly pull the target columns and rename neatly
                df_view = df_view[["Label", "DateNoticed", "PrecipNoticed", "Comments"]]
                df_view.columns = ["Leak Description", "Date Noticed", "Precipitation", "Comments / Notes"]
                
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            except Exception as table_err:
                st.caption("Unable to format history grid columns. Raw attributes might be initializing.")
