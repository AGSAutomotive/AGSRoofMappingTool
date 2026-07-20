import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw, ImageFont  
import time
import io
import datetime
from zoneinfo import ZoneInfo  
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
st.info("💡Select plant from the dropdown and enter your AGS email. Then click anywhere on the **floor map** image to plot a leak. Scroll down to edit more details, attach photos, and submit a report.")

# 1. User & Plant Info Inputs
col_p1, col_p2 = st.columns([4.0, 6.0])
with col_p1:
    plant = st.selectbox("Select Plant:", ['Cambridge - 07', 'Oshawa - 04', 'Sterling 18.5', 'Sterling South', 'Windsor - 02'])
    plant_key = plant.replace(' ', '_').replace('-', '_').replace('.', '_')
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
        'Sterling 18.5': {"lat": 42.542228, "lon": -83.041669},
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
    elif plant == "Sterling 18.5":
        left_path, right_path = "data/Sterling18.5CAD.png", "data/Sterling18.5.png"
    elif "Sterling" in plant:
        left_path, right_path = "data/SterlingSouthCAD.png", "data/SterlingSouth.png"
    else:
        left_path, right_path = "data/WindsorCAD.png", "data/Windsor.png"

    left_img = Image.open(left_path).convert("RGB")
    right_img = Image.open(right_path).convert("RGB")
    
    DISPLAY_WIDTH = 1200
    left_resized = left_img.resize((DISPLAY_WIDTH, int(left_img.height * (DISPLAY_WIDTH / left_img.width))))
    right_resized = right_img.resize((DISPLAY_WIDTH, int(right_img.height * (DISPLAY_WIDTH / right_img.width))))
except Exception as e:
    st.error(f"⚠️ Base asset missing inside data/ directory: {e}")
    st.stop()

# Font Configuration Setup
try:
    font_floor = ImageFont.load_default(size=16)     # Target size for both Floor and Roof layouts
    font_history = ImageFont.load_default(size=24)   
except Exception:
    font_floor = ImageFont.load_default()
    font_history = ImageFont.load_default()

left_display = left_resized.copy()
right_display = right_resized.copy()
draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

excel_overlay_canvas = Image.new("RGBA", right_resized.size, (255, 255, 255, 0))
draw_excel = ImageDraw.Draw(excel_overlay_canvas)

for pt in st.session_state["new_pins_batch"]:
    x, y, custom_name = pt['x'], pt['y'], pt['name']
    
    # 🗺️ FLOOR MAP VIEW (Size 16 Text Block)
    draw_left.ellipse((x-8, y-8, x+8, y+8), fill="red")
    text_pos_left = (x + 14, y - 10)
    bbox_left = draw_left.textbbox(text_pos_left, custom_name, font=font_floor)
    draw_left.rectangle((bbox_left[0]-5, bbox_left[1]-3, bbox_left[2]+5, bbox_left[3]+3), fill="white", outline="red", width=2)
    draw_left.text(text_pos_left, custom_name, fill="red", font=font_floor)
    
    # 🦅 UPDATED: ROOF VIEW MAP (Now matched precisely to size 16 text constraints)
    draw_right.ellipse((x-24, y-24, x+24, y+24), outline="cyan", width=4)
    draw_right.ellipse((x-6, y-6, x+6, y+6), fill="red")
    text_pos_right = (x + 30, y - 10)
    bbox_right = draw_right.textbbox(text_pos_right, custom_name, font=font_floor)
    draw_right.rectangle((bbox_right[0]-5, bbox_right[1]-3, bbox_right[2]+5, bbox_right[3]+3), fill="#1A1A1A", outline="cyan", width=2)
    draw_right.text(text_pos_right, custom_name, fill="cyan", font=font_floor)

    # 🔗 UPDATED: Transparent Database Overlay (Keeps backend maps matching layout changes)
    draw_excel.ellipse((x-24, y-24, x+24, y+24), outline="cyan", width=4)
    draw_excel.ellipse((x-6, y-6, x+6, y+6), fill="red")
    draw_excel.rectangle((bbox_right[0]-5, bbox_right[1]-3, bbox_right[2]+5, bbox_right[3]+3), fill="#1A1A1A", outline="cyan", width=2)
    draw_excel.text(text_pos_right, custom_name, fill="cyan", font=font_floor)

st.write("---")
st.subheader("🗺️ Floor Map (Click to Plot Leak)")
click = streamlit_image_coordinates(left_display, key=f"click_{plant_key}")

if click and click != st.session_state.get(f"lclick_{plant_key}"):
    st.session_state[f"lclick_{plant_key}"] = click
    next_serial = len(st.session_state["new_pins_batch"]) + 1
    
    st.session_state["new_pins_batch"].append({
        'id': str(time.time()).replace(".", ""), 
        'serial': next_serial, 'x': click['x'], 'y': click['y'],
        'name': f"Leak Point {next_serial}", 'start_date': datetime.date.today(),
        'comments': "",
        'photo1_name': "", 'photo1_base64': "", 'photo1_ext': "",
        'photo2_name': "", 'photo2_base64': "", 'photo2_ext': ""
    })
    st.rerun()

st.write("---")
st.subheader("🦅 Roof View")
st.image(right_display)

# --- Grid Form Layout Area ---
st.write("---")
st.subheader("📋 New Unreported Leaks")

if not st.session_state["new_pins_batch"]:
    st.info("💡No new leaks plotted yet for this plant. Click on the floor map above to plot new leaks.")
else:
    st.info("💡**Click to rename or add details:** Customize the leak label, date, add comments, and upload up to two photos below.")
    
    # Rebalanced grid columns to support image upload inputs cleanly
    grid_header1, grid_header2, grid_header3, grid_header4, grid_header5, grid_header6, grid_header7, grid_header8 = st.columns([0.6, 1.4, 1.2, 1.3, 1.3, 1.8, 1.8, 0.8])
    with grid_header3: st.markdown("**📅 Date Noticed**")
    with grid_header4: st.markdown("**🌦️ Precip. (Day)**")
    with grid_header5: st.markdown("**🌦️ Precip. (Day Before)**")
    with grid_header6: st.markdown("**💬 Comments / Notes**")
    with grid_header7: st.markdown("**📸 Attach Photos (Max 2)**")

    for index, point in enumerate(st.session_state["new_pins_batch"]):
        if 'comments' not in point:
            st.session_state["new_pins_batch"][index]['comments'] = ""
        if 'photo1_name' not in point: st.session_state["new_pins_batch"][index]['photo1_name'] = ""
        if 'photo1_base64' not in point: st.session_state["new_pins_batch"][index]['photo1_base64'] = ""
        if 'photo1_ext' not in point: st.session_state["new_pins_batch"][index]['photo1_ext'] = ""
        if 'photo2_name' not in point: st.session_state["new_pins_batch"][index]['photo2_name'] = ""
        if 'photo2_base64' not in point: st.session_state["new_pins_batch"][index]['photo2_base64'] = ""
        if 'photo2_ext' not in point: st.session_state["new_pins_batch"][index]['photo2_ext'] = ""
            
        c_idx, c_lbl, c_dt, c_w1, c_w2, c_cmt, c_photos, c_del = st.columns([0.6, 1.4, 1.2, 1.3, 1.3, 1.8, 1.8, 0.8])
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
        
        with c_cmt:
            new_comment = st.text_input("Comments:", value=point['comments'], placeholder="e.g., Near stamping press, pooling", key=f"cmt_{point['id']}", label_visibility="collapsed")
            if new_comment != point['comments']:
                st.session_state["new_pins_batch"][index]['comments'] = new_comment
                st.rerun()

        with c_photos:
            uploaded_files = st.file_uploader("Upload photos:", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"photos_{point['id']}", label_visibility="collapsed")
            if uploaded_files:
                # Limit to maximum 2 photos
                valid_files = uploaded_files[:2]
                if len(uploaded_files) > 2:
                    st.warning("⚠️ Only the first 2 photos will be stored.")
                
                # Encode file 1
                if len(valid_files) >= 1:
                    f1 = valid_files[0]
                    f1_bytes = f1.getvalue()
                    ext1 = f1.name.split('.')[-1] if '.' in f1.name else 'jpg'
                    st.session_state["new_pins_batch"][index]['photo1_name'] = f1.name
                    st.session_state["new_pins_batch"][index]['photo1_ext'] = ext1
                    st.session_state["new_pins_batch"][index]['photo1_base64'] = base64.b64encode(f1_bytes).decode('utf-8')
                else:
                    st.session_state["new_pins_batch"][index]['photo1_name'] = ""
                    st.session_state["new_pins_batch"][index]['photo1_ext'] = ""
                    st.session_state["new_pins_batch"][index]['photo1_base64'] = ""
                
                # Encode file 2
                if len(valid_files) >= 2:
                    f2 = valid_files[1]
                    f2_bytes = f2.getvalue()
                    ext2 = f2.name.split('.')[-1] if '.' in f2.name else 'jpg'
                    st.session_state["new_pins_batch"][index]['photo2_name'] = f2.name
                    st.session_state["new_pins_batch"][index]['photo2_ext'] = ext2
                    st.session_state["new_pins_batch"][index]['photo2_base64'] = base64.b64encode(f2_bytes).decode('utf-8')
                else:
                    st.session_state["new_pins_batch"][index]['photo2_name'] = ""
                    st.session_state["new_pins_batch"][index]['photo2_ext'] = ""
                    st.session_state["new_pins_batch"][index]['photo2_base64'] = ""
            else:
                # Clear references if files are removed
                st.session_state["new_pins_batch"][index]['photo1_name'] = ""
                st.session_state["new_pins_batch"][index]['photo1_ext'] = ""
                st.session_state["new_pins_batch"][index]['photo1_base64'] = ""
                st.session_state["new_pins_batch"][index]['photo2_name'] = ""
                st.session_state["new_pins_batch"][index]['photo2_ext'] = ""
                st.session_state["new_pins_batch"][index]['photo2_base64'] = ""
        
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
        st.info("💡Once all new leaks are plotted and configured, click the **'Report Leaks'** button below to submit.")
    
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
                
                grid_positions = {'Cambridge___07': "A2", 'Oshawa___04': "M2", 'Sterling_18_5': "AW2", 'Sterling_South': "AK2", 'Windsor___02': "Y2"}
                target_cell = grid_positions.get(plant_key, "A2")
                
                leak_items_list = []
                email_attachments_list = []
                
                for pt in st.session_state["new_pins_batch"]:
                    c_date = pt['start_date']
                    lbl_name = pt['name']
                    
                    stored_x = int(pt['x'] * (600 / DISPLAY_WIDTH))
                    stored_y = int(pt['y'] * (int(left_img.height * (600 / left_img.width)) / int(left_img.height * (DISPLAY_WIDTH / left_img.width))))
                    
                    leak_items_list.append({
                        "Serial": int(pt['serial']),
                        "Label": lbl_name,
                        "DateNoticed": c_date.strftime("%Y-%m-%d"),
                        "PrecipNoticed": get_real_weather_data(plant, c_date),
                        "PrecipBefore": get_real_weather_data(plant, c_date - datetime.timedelta(days=1)),
                        "CoordinateX": stored_x,
                        "CoordinateY": stored_y,
                        "Comments": pt.get('comments', "").strip(),
                        "Photo1_Name": pt.get('photo1_name', ""),
                        "Photo1_Base64": pt.get('photo1_base64', ""),
                        "Photo2_Name": pt.get('photo2_name', ""),
                        "Photo2_Base64": pt.get('photo2_base64', "")
                    })
                    
                    # Package Photo 1 as an explicit top-level attachment array item
                    if pt.get('photo1_base64'):
                        p1_ext = pt.get('photo1_ext', 'jpg')
                        email_attachments_list.append({
                            "Name": f"{lbl_name} - Photo1.{p1_ext}",
                            "ContentBytes": pt['photo1_base64']
                        })
                        
                    # Package Photo 2 as an explicit top-level attachment array item
                    if pt.get('photo2_base64'):
                        p2_ext = pt.get('photo2_ext', 'jpg')
                        email_attachments_list.append({
                            "Name": f"{lbl_name} - Photo2.{p2_ext}",
                            "ContentBytes": pt['photo2_base64']
                        })
                
                raw_df = pd.DataFrame(leak_items_list)
                email_df = raw_df.drop(columns=["Serial", "CoordinateX", "CoordinateY", "Photo1_Base64", "Photo2_Base64"], errors="ignore")
                
                # Dynamically represent attachment indicators in the email notification table
                email_df['Photo 1'] = email_df['Photo1_Name'].apply(lambda x: "📎 Attached" if x else "None")
                email_df['Photo 2'] = email_df['Photo2_Name'].apply(lambda x: "📎 Attached" if x else "None")
                email_df = email_df.drop(columns=["Photo1_Name", "Photo2_Name"], errors="ignore")
                
                email_df.columns = ["Leak Description", "Date Noticed", "Precipitation (Day)", "Precipitation (Before)", "Comments / Actions", "Photo 1", "Photo 2"]
                
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
                    "EmailTableHTML": styled_email_table,
                    "EmailAttachments": email_attachments_list
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
with st.expander("🔒 History (Live Database Sync)", expanded=True):
    st.subheader(f"📊 Historical Leak Records — {plant}")
    
    historical_records = []
    try:
        response = requests.get(f"{EXCEL_FETCH_URL}&cb={time.time()}", timeout=60)
        if response.status_code == 200:
            historical_records = response.json()
            if not isinstance(historical_records, list):
                historical_records = response.json().get("value", [])
    except Exception as e:
        st.error("⚠️ Failed to communicate with live Power Automate database retriever flow.")

    plant_historical_records = []
    for r in historical_records:
        if str(r.get("Plant", "")).strip() == plant:
            plant_historical_records.append(r)

    # Convert the dynamic fetched historical records to a DataFrame
    if plant_historical_records:
        hist_df = pd.DataFrame(plant_historical_records)
        
        # --- 🔧 DATE FORMAT FIX BLOCK ---
        # Handles raw Excel serial numbers (e.g., 45431), numeric epochs, and standard strings
        if "DateNoticed" in hist_df.columns:
            try:
                def parse_excel_date(val):
                    if pd.isna(val) or str(val).strip() == "":
                        return "N/A"
                    try:
                        # Convert to numeric to check if it's an Excel serial date
                        num_val = float(val)
                        # Excel dates in the 2000s-2020s typically fall between 35000 and 60000
                        if 30000 < num_val < 60000:
                            return (pd.to_datetime("1899-12-30") + pd.to_timedelta(num_val, unit="D")).strftime('%Y-%m-%d')
                        # If it's a giant Unix timestamp code instead
                        elif num_val > 1000000000:
                            return pd.to_datetime(num_val, unit='ms' if num_val > 100000000000 else 's', errors='coerce').strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
                    
                    # Fallback to standard string date parsing if it's not a raw number
                    try:
                        parsed_dt = pd.to_datetime(val, errors='coerce')
                        if pd.notna(parsed_dt):
                            return parsed_dt.strftime('%Y-%m-%d')
                    except:
                        pass
                    
                    return str(val)

                hist_df["DateNoticed"] = hist_df["DateNoticed"].apply(parse_excel_date)
            except Exception as dt_err:
                hist_df["DateNoticed"] = hist_df["DateNoticed"].astype(str)
    
        # --- 🗺️ PLOT HISTORICAL COORDINATES ON THE ROOF MAP ---
        hist_map_image = right_resized.copy()
        draw_hist = ImageDraw.Draw(hist_map_image)
        
        for index, row in hist_df.iterrows():
            try:
                # Retrieve coordinates safely from database structure
                db_x = row.get("CoordinateX")
                db_y = row.get("CoordinateY")
                label = str(row.get("Label", f"Leak {index + 1}"))
                
                if db_x is not None and db_y is not None:
                    # Convert coordinates back from the 600px stored format to layout display width
                    hist_x = int(float(db_x) * (DISPLAY_WIDTH / 600))
                    hist_y = int(float(db_y) * (int(left_img.height * (DISPLAY_WIDTH / left_img.width)) / int(left_img.height * (600 / left_img.width))))
                    
                    # Draw pins matching exact style definitions
                    draw_hist.ellipse((hist_x - 24, hist_y - 24, hist_x + 24, hist_y + 24), outline="cyan", width=4)
                    draw_hist.ellipse((hist_x - 6, hist_y - 6, hist_x + 6, hist_y + 6), fill="red")
                    
                    text_pos = (hist_x + 30, hist_y - 10)
                    bbox = draw_hist.textbbox(text_pos, label, font=font_floor)
                    draw_hist.rectangle((bbox[0] - 5, bbox[1] - 3, bbox[2] + 5, bbox[3] + 3), fill="#1A1A1A", outline="cyan", width=2)
                    draw_hist.text(text_pos, label, fill="cyan", font=font_floor)
            except Exception as plot_err:
                pass
                
        # --- Create Two Columns inside the Expander (Map Left, Table Right) ---
        col_hist_left, col_hist_right = st.columns([4.0, 6.0])
        
        with col_hist_left:
            # Render a smaller, neat historical map (using layout width constraints inside column)
            st.image(hist_map_image, use_container_width=True)
            
        with col_hist_right:
            st.markdown("### 📋 Database Records")
            
            # Select, organize, and rename only the specific columns requested
            col_mapping = {
                "Label": "Label",
                "DateNoticed": "Date Noticed",
                "PrecipNoticed": "Precip. (Day)",
                "PrecipBefore": "Precip. (Day Before)",
                "ReporterEmail": "Reporter Email",
                "Comments": "Comments"
            }
            
            # Filter the dataframe safely matching columns that actually exist in your fetched data
            existing_cols = [c for c in col_mapping.keys() if c in hist_df.columns]
            filtered_df = hist_df[existing_cols].rename(columns=col_mapping)
            
            # Display clean table
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    else:
        st.info("🍃 The historical database is currently empty for this plant.")
