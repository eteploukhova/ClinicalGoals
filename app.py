import streamlit as st
import json
import re

# Set page configuration
st.set_page_config(page_title="RT Clinical Goals Viewer", layout="wide")

@st.cache_data
def load_data():
    with open('clinicalGoals_by_anatomical_sites.json', 'r') as f:
        return json.load(f)

def clean_goal_string(gs):
    """Applies visual improvements to the goal string."""
    if not gs:
        return ""
    # 1. Substitute symbols
    gs = gs.replace("<=", "≤").replace(">=", "≥")
    # 2. Fix cm3 notation
    gs = gs.replace("cm3", "cm³").replace("cc", "cm³")
    # 3. Remove text in parentheses (like '(mandatory)')
    gs = re.sub(r'\(.*?\)', '', gs).strip()
    return gs

try:
    data = load_data()
except Exception as e:
    st.error(f"Error loading JSON: {e}")
    st.stop()

st.title("🎯 RT Clinical Goals Explorer")

# --- SIDEBAR ---
st.sidebar.header("Filter Criteria")
sites = sorted(list(data["treatmentSites"].keys()))
selected_site = st.sidebar.selectbox("1. Treatment Site", sites)

frac_types = list(data["treatmentSites"][selected_site]["fractionations"].keys())
selected_type = st.sidebar.selectbox("2. Fractionation Type", frac_types)

path = data["treatmentSites"][selected_site]["fractionations"][selected_type]

if selected_type == "hypofractionated":
    num_fractions = sorted(list(path.keys()), key=int)
    selected_num = st.sidebar.selectbox("3. Number of Fractions", num_fractions)
    goal_sets = path[selected_num]["clinicalGoalSets"]
else:
    goal_sets = path["clinicalGoalSets"]

goal_set_names = [gs["name"] for gs in goal_sets]
selected_gs_name = st.sidebar.selectbox("4. Publication/Set", goal_set_names)
current_goal_set = next(gs for gs in goal_sets if gs["name"] == selected_gs_name)

# --- MAIN DISPLAY ---
st.subheader(f"Dataset: {current_goal_set['name']}")
if "doi" in current_goal_set:
    st.info(f"🔗 **DOI:** [https://doi.org/{current_goal_set['doi']}](https://doi.org/{current_goal_set['doi']})")

table_data = []
for g in current_goal_set["goals"]:
    table_data.append({
        "ROI (Organ)": g["roi"],
        "Clinical Goal": clean_goal_string(g["goal_str"]), # Applied cleaning here
        "Priority": g["priority"].upper() if g["priority"] else "---",
        "Notes": g["notes"]
    })

# Render the table
st.table(table_data)