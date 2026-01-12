import streamlit as st
import json
import re

# Set page configuration
st.set_page_config(page_title="RT Clinical Goals Viewer", layout="wide")

@st.cache_data
def load_data():
    with open('clinicalGoals_by_anatomical_sites.json', 'r') as f:
        return json.load(f)

def clean_text_symbols(text):
    """Replaces symbols and units in standard text (Notes column)."""
    if not text:
        return ""
    # Replace symbols
    text = text.replace("<=", "≤").replace(">=", "≥")
    # Replace cm3/cc with proper superscript
    text = text.replace("cm3", "cm³").replace("cc", "cm³")
    return text

def format_goal_latex(gs):
    """
    Transforms goal strings into professional scientific notation.
    Moves units (Gy, %, cm3) into subscripts when attached to V or D.
    """
    if not gs:
        return ""
    
    # 1. Remove text in parentheses (e.g., '(mandatory)')
    gs = re.sub(r'\(.*?\)', '', gs).strip()
    
    # 2. Normalize symbols for math mode
    gs = gs.replace("<=", r" \le ").replace(">=", r" \ge ").replace("<", " < ").replace(">", " > ")

    # 3. Convert units to LaTeX style
    gs = gs.replace("cm3", r"\text{ cm}^3").replace("cc", r"\text{ cm}^3")
    gs = gs.replace("%", r"\%")
    gs = gs.replace("Gy", r"\text{ Gy}")

    # 4. Handle Dmax and Dmean (subscript the text)
    gs = re.sub(r'DMAX', r'D_{max}', gs, flags=re.IGNORECASE)
    gs = re.sub(r'DMEAN', r'D_{mean}', gs, flags=re.IGNORECASE)

    # 5. Professional Subscripting for V and D
    # V subscript: Capture number + unit immediately following V
    gs = re.sub(r'V(\d+\.?\d*)\s*(\\text\{ Gy\}|\\%)', r'V_{\1\2}', gs)
    
    # D subscript: Capture number + unit (cm3 or %) immediately following D
    gs = re.sub(r'D(\d+\.?\d*)\s*(\\text\{ cm\}\^3|\\%)', r'D_{\1\2}', gs)
    
    # Catch any remaining V or D numbers without units that haven't been subscripted
    gs = re.sub(r'(?<!_)([VD])(\d+\.?\d*)', r'\1_{\2}', gs)

    return f"${gs}$"

# --- APPLICATION START ---

try:
    data = load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

st.title("🎯 RT Clinical Goals Explorer")
st.markdown("---")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Criteria")

# 1. Site Selection
sites = sorted(list(data["treatmentSites"].keys()))
selected_site = st.sidebar.selectbox("1. Treatment Site", sites)

# 2. Fractionation Selection (Capitalized)
frac_options = list(data["treatmentSites"][selected_site]["fractionations"].keys())
# Map capitalized display names to the original keys
frac_display_map = {f.capitalize(): f for f in frac_options}
selected_frac_display = st.sidebar.selectbox("2. Fractionation Type", list(frac_display_map.keys()))
selected_type = frac_display_map[selected_frac_display]

path = data["treatmentSites"][selected_site]["fractionations"][selected_type]

# Handle hypofractionated sub-layers
if selected_type == "hypofractionated":
    num_fractions = sorted(list(path.keys()), key=int)
    selected_num = st.sidebar.selectbox("3. Number of Fractions", num_fractions)
    goal_sets = path[selected_num]["clinicalGoalSets"]
else:
    goal_sets = path["clinicalGoalSets"]

# 4. Publication Selection
goal_set_names = [gs["name"] for gs in goal_sets]
selected_gs_name = st.sidebar.selectbox("4. Publication Reference", goal_set_names)
current_goal_set = next(gs for gs in goal_sets if gs["name"] == selected_gs_name)

# --- HEADER SECTION ---
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"Dataset: {current_goal_set['name']}")
    if "doi" in current_goal_set:
        st.caption(f"🔗 DOI: [https://doi.org/{current_goal_set['doi']}](https://doi.org/{current_goal_set['doi']})")
with col2:
    st.metric("Constraints", len(current_goal_set["goals"]))

# --- TABLE DISPLAY ---
st.markdown("""
<style>
    .mandatory { color: #b91c1c; font-weight: bold; }
    .optimal { color: #15803d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Build Markdown Table
markdown_table = "| ROI (Organ) | Clinical Goal | Priority | Notes |\n| :--- | :--- | :--- | :--- |\n"

for g in current_goal_set["goals"]:
    roi = f"**{g['roi']}**"
    goal = format_goal_latex(g['goal_str'])
    
    # Priority styling
    p_val = g['priority'].lower()
    if 'mandatory' in p_val:
        priority = "<span class='mandatory'>MANDATORY</span>"
    elif 'optimal' in p_val:
        priority = "<span class='optimal'>OPTIMAL</span>"
    else:
        priority = "---"
        
    # Clean up symbols and units in Notes
    notes = clean_text_symbols(g['notes'])
    
    markdown_table += f"| {roi} | {goal} | {priority} | {notes} |\n"

st.markdown(markdown_table, unsafe_allow_html=True)

st.divider()
st.caption("UI version 1.2: Fixed text symbols and capitalization.")