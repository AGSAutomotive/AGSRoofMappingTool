import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import time
import io
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Set up page layout
st.set_page_config(page_title="AGS Roof Leak Mapper", layout="wide")
st.title("🏭 AGS Roof Leak Mapping Tool")
st.write("Click on the left floor view to add a leak point. Use the dashboard below to manage labels and export everything directly to Excel.")

# 1. Plant Selection
plant = st.selectbox("Select Manufacturing Plant:", ["Plant 1", "Plant 2", "Plant 3"])

# Image pathways (Desk on left, Ceiling on right)
if plant == "Plant 1":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
elif plant == "Plant 2":
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"
else:
    left_path = "data/Desk (under roof).jpg"
    right_path = "data/Office Ceiling (Roof).jpg"

# 2. Safely Load and Resize Images
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
    st.error("⚠️ Could not find the image files. Please ensure 'Office Ceiling (Roof).jpg' and 'Desk (under roof).jpg' exist inside the 'data/' folder.")
    st.stop()

# Initialize session state tracking list for the active plant
if f"leak_points_{plant}" not in st.session_state:
    st.session_state[f"leak_points_{plant}"] = []

# Persistent counter ensures leak numbers never repeat or shift down on deletion
if f"point_counter_{plant}" not in st.session_state:
    st.session_state[f"point_counter_{plant}"] = 1

# Keep track of the temporary last click to catch new interactions
if f"last_click_{plant}" not in st.session_state:
    st.session_state[f"last_click_{plant}"] = None

# 3. Prepare Image Overlays (Draw all currently active points)
left_display = left_resized.copy()
right_display = right_resized.copy()

draw_left = ImageDraw.Draw(left_display)
draw_right = ImageDraw.Draw(right_display)

# Draw all existing saved points onto both images using their custom text names
for pt in st.session_state[f"leak_points_{plant}"]:
    x, y = pt['x'], pt['y']
    custom_name = pt['name']
    
    # Left View Indicators (Solid Red Dots mapped to custom text name)
    draw_left.ellipse((x - 6, y - 6, x + 6, y + 6), fill="red")
    draw_left.text((x + 8, y - 6), custom_name, fill="yellow")
    
    # Right View Indicators (Cyan Target Rings mapped to identical custom text name)
    draw_right.ellipse((x - 12, y - 12, x + 12, y + 12), outline="cyan", width=3)
    draw_right.ellipse((x - 3, y - 3, x + 3, y + 3), fill="red")
    draw_right.text((x + 14, y - 12), custom_name, fill="cyan")

# 4. Display Side-by-Side Views
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Floor Map View (Click Here)")
    clicked_coords = streamlit_image_coordinates(
        left_display,
        key=f"image_click_{plant}" 
    )
    
    # Process if a brand new click location is registered
    if clicked_coords is not None and clicked_coords != st.session_state[f"last_click_{plant}"]:
        st.session_state[f"last_click_{plant}"] = clicked_coords
        
        current_serial = st.session_state[f"point_counter_{plant}"]
        unique_timestamp_id = str(time.time()).replace(".", "")
        
        st.session_state[f"leak_points_{plant}"].append({
            'id': unique_timestamp_id,
            'serial': current_serial,
            'x': clicked_coords['x'],
            'y': clicked_coords['y'],
            'name': f"Leak Point {current_serial}"
        })
        
        st.session_state[f"point_counter_{plant}"] += 1
        st.rerun()

with col2:
    st.subheader("🦅 Corresponding Roof View")
    st.image(right_display, use_container_width=False)


# --- FUNCTION TO EXCEL WITH IMAGES ---
def export_to_excel_with_images(points, left_img_obj, right_img_obj, plant_name):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leak Mapping Report"
    
    # Setup grid formatting visibility
    ws.views.sheetView[0].showGridLines = True
    
    # Design Theme Styles
    navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    accent_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
    white_bold = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    navy_bold = Font(name="Calibri", size=11, bold=True, color="1F497D")
    regular_font = Font(name="Calibri", size=11)
    
    thin_border = Border(
        left=Side(style='thin', color='BFBFBF'),
        right=Side(style='thin', color='BFBFBF'),
        top=Side(style='thin', color='BFBFBF'),
        bottom=Side(style='thin', color='BFBFBF')
    )
    
    # Title Block
    ws.merge_cells("A1:D1")
    ws["A1"] = f"AGS Leak Mapping Report - {plant_name}"
    ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="1F497D")
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30
    
    # Data Table Headers
    headers = ["Point ID", "Custom Label", "Coordinate X", "Coordinate Y"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.fill = navy_fill
        cell.font = white_bold
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[3].height = 24
    
    # Populate Data rows
    start_row = 4
    for idx, pt in enumerate(points):
        current_row = start_row + idx
        ws.row_dimensions[current_row].height = 20
        
        c1 = ws.cell(row=current_row, column=1, value=f"#{pt['serial']}")
        c2 = ws.cell(row=current_row, column=2, value=pt['name'])
        c3 = ws.cell(row=current_row, column=3, value=int(pt['x']))
        c4 = ws.cell(row=current_row, column=4, value=int(pt['y']))
        
        for cell in [c1, c2, c3, c4]:
            cell.font = regular_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
    # Auto-adjust column widths for data
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)
        
    # --- IMAGE PLACEMENT SECTION ---
    image_heading_row = start_row + len(points) + 2
    
    # Left Map Header
    ws.cell(row=image_heading_row, column=1, value="🗺️ Final Marked Floor Map View").font = navy_bold
    # Right Map Header
    ws.cell(row=image_heading_row, column=6, value="🦅 Final Corresponding Roof View").font = navy_bold
    
    # Save PIL images out to memory byte buffers to inject into openpyxl
    left_buffer = io.BytesIO()
    right_buffer = io.BytesIO()
    
    # Resize slightly for clean fitting inside standard Excel columns
    left_img_obj.resize((450, int(left_img_obj.height * (450/left_img_obj.width)))).save(left_buffer, format="JPEG")
    right_img_obj.resize((450, int(right_img_obj.height * (450/right_img_obj.width)))).save(right_buffer, format="JPEG")
    
    left_buffer.seek(0)
    right_buffer.seek(0)
    
    xl_img_left = OpenpyxlImage(left_buffer)
    xl_img_right = OpenpyxlImage(right_buffer)
    
    # Anchor the image placements to top-left corners of designated target cell grids
    ws.add_image(xl_img_left, f"A{image_heading_row + 1}")
    ws.add_image(xl_img_right, f"F{image_heading_row + 1}")
    
    # Output to virtual workbook stream
    output_stream = io.BytesIO()
    wb.save(output_stream)
    output_stream.seek(0)
    return output_stream


# --- 📋 TRACKING LIST & MANAGEMENT DASHBOARD ---
st.write("---")
st.subheader("📋 Saved Leak Records Dashboard")

points_list = st.session_state[f"leak_points_{plant}"]

if not points_list:
    st.info("💡 No leaks mapped yet. Click on the left Floor Map image to begin pinning locations.")
else:
    # Build control rows for editing items individually
    for index, point in enumerate(points_list):
        edit_col1, edit_col2, edit_col3 = st.columns([1.5, 3, 2])
        
        with edit_col1:
            st.write(f"**Point #{point['serial']}** (X:{int(point['x'])}, Y:{int(point['y'])})")
            
        with edit_col2:
            new_name = st.text_input(
                "Rename label:", 
                value=point['name'], 
                key=f"rename_{plant}_{point['id']}",
                label_visibility="collapsed"
            )
            if new_name != point['name']:
                st.session_state[f"leak_points_{plant}"][index]['name'] = new_name
                st.rerun()
                
        with edit_col3:
            if st.button("🗑️ Delete Record", key=f"del_{plant}_{point['id']}"):
                st.session_state[f"leak_points_{plant}"].pop(index)
                st.rerun()
                
    # EXPORT ACTION AREA
    st.write("---")
    st.markdown("### 📤 Export Layout Data")
    
    # Process the binary excel workbook sheet generation loop
    excel_data = export_to_excel_with_images(
        points_list, 
        left_display, 
        right_display, 
        plant
    )
    
    # Standard Native download interaction stream 
    st.download_button(
        label="📥 Download Data & Maps to Excel (.xlsx)",
        data=excel_data,
        file_name=f"AGS_Leak_Report_{plant.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
