import streamlit as st
import json

# Set page configuration
st.set_page_config(page_title="RT Clinical Goals Viewer", layout="wide")

# Load the JSON data
@st.cache_data
def load_data():
    with open('clinicalGoals_by_anatomical_sites.json', 'r') as f:
        return json.load(f)

try:
    data = load_data()
except FileNotFoundError:
    st.error("JSON file not found. Please ensure 'clinicalGoals_by_anatomical_sites.json' is in the same folder.")
    st.stop()

st.title("🎯 RT Clinical Goals Explorer")
st.markdown("Use the filters on the left to browse site-specific clinical goals.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Criteria")

# 1. Treatment Site
sites = sorted(list(data["treatmentSites"].keys()))
selected_site = st.sidebar.selectbox("1. Select Treatment Site", sites)

# 2. Fractionation Type
frac_types = list(data["treatmentSites"][selected_site]["fractionations"].keys())
selected_type = st.sidebar.selectbox("2. Select Fractionation Type", frac_types)

# 3. Handle Hypofractionated Sub-menu (Number of Fractions)
# The JSON structure for hypofractionated has an extra level for number of fractions
path = data["treatmentSites"][selected_site]["fractionations"][selected_type]

if selected_type == "hypofractionated":
    num_fractions = sorted(list(path.keys()), key=int)
    selected_num = st.sidebar.selectbox("3. Number of Fractions", num_fractions)
    goal_sets = path[selected_num]["clinicalGoalSets"]
else:
    # Conventional fractionation
    goal_sets = path["clinicalGoalSets"]

# 4. Goal Set (Publication)
goal_set_names = [gs["name"] for gs in goal_sets]
selected_gs_name = st.sidebar.selectbox("4. Select Goal Set / Publication", goal_set_names)

# Find the specific goal set object
current_goal_set = next(gs for gs in goal_sets if gs["name"] == selected_gs_name)

# --- MAIN DISPLAY ---

# Display Publication Info
st.subheader(f"Dataset: {current_goal_set['name']}")
if "doi" in current_goal_set:
    url = f"https://doi.org/{current_goal_set['doi']}"
    st.info(f"🔗 **Source Publication (DOI):** [{current_goal_set['doi']}]({url})")

# Prepare and Display Table
st.write("### Clinical Goals List")

table_data = []
for g in current_goal_set["goals"]:
    table_data.append({
        "ROI (Organ)": g["roi"],
        "Clinical Goal": g["goal_str"], # Uses the readable format from your JSON
        "Priority": g["priority"].capitalize() if g["priority"] else "Standard",
        "Notes": g["notes"]
    })

# Render the interactive table
st.dataframe(table_data, use_container_width=True, hide_index=True)

# Footer
st.divider()
st.caption("Data source: clinicalGoals_by_anatomical_sites.json")