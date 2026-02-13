import streamlit as st
import google.generativeai as genai
import json
import re
import copy
from streamlit_echarts import st_echarts

# --- Page Configuration ---
st.set_page_config(
    page_title="Overthinker Guide",
    page_icon="🧠",
    layout="wide"
)

# --- Modern UI Styling ---
st.markdown("""
<style>
    /* Main app background */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .main {
        background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5664);
        color: #FFFFFF;
    }
    /* Text input box */
    .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.05);
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        font-size: 16px;
    }
    /* Buttons */
    .stButton button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: bold;
        padding: 12px 24px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    /* Headers */
    h1, h2, h3 {
        color: #FFFFFF;
        text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.5);
        text-align: center;
    }
    /* Summary Box */
    .summary-box {
        background: rgba(102, 126, 234, 0.15);
        border-left: 5px solid #667eea;
        border-radius: 10px;
        padding: 20px 25px;
        margin-top: 20px;
        font-size: 1.15em;
        color: #FFFFFF;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# --- Gemini API Configuration ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("🚨 GOOGLE_API_KEY not found. Please add it to your .streamlit/secrets.toml file.", icon="❗")
    st.stop()

# --- AI Prompt Templates ---
PROMPT_INITIAL = """
You are 'Overthinker Guide', an AI that helps people analyze situations they're overthinking.
The user is worried about: "{user_scenario}"

Generate a JSON object with "tree" and "summary".

1. **tree**: A root node with the situation as 'name', 'description' ("Explore the possible outcomes"), 'path' ("root"), and 'children'. 
   The 'children' must be EXACTLY 3 outcomes:
   - Best Case Scenario
   - Most Likely/Expected Scenario  
   - Worst Case Scenario
   
   Each child must have:
   - 'name': The outcome type (e.g., "Best Case Scenario")
   - 'description': A concise 1-2 sentence description of this outcome for the situation
   - 'path': A unique string ("0" for best, "1" for expected, "2" for worst)
   - 'children': An empty list `[]`

2. **summary**: A calming, reassuring paragraph that acknowledges their concern and provides perspective on the situation.

**CONSTRAINTS:**
- Output ONLY the raw JSON object
- No markdown formatting in JSON values
- Keep descriptions brief and realistic

---
User's Situation: "{user_scenario}"
Your JSON Output:
"""

PROMPT_EXPAND = """
You are 'Overthinker Guide'. The user is exploring a specific outcome branch.
Initial Situation: "{user_scenario}"
Current Outcome: "{path_name}"
Current Description: "{path_description}"

Generate a JSON object with "children" containing 2-4 detailed sub-outcomes or consequences of this scenario.
Each child must have:
- 'name': A specific consequence or aspect
- 'description': A brief 1-2 sentence explanation
- 'path': A unique path string (e.g., "{parent_path}-0")
- 'children': An empty list `[]`

Be realistic and balanced. Help the user see concrete details without catastrophizing.

**CONSTRAINTS:**
- Output ONLY the raw JSON object
- No markdown formatting

---
Your JSON Output:
"""

# --- Helper Functions ---
def robust_json_parser(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match: return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

def call_gemini_api(prompt, retries=2):
    """Calls the Gemini API with error handling."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    for attempt in range(retries + 1):
        try:
            response = model.generate_content(prompt)
            return robust_json_parser(response.text)
        except Exception as e:
            if attempt >= retries:
                st.error(f"API call failed after {retries + 1} attempts: {e}", icon="🕸️")
                return None
            st.warning(f"API call failed on attempt {attempt + 1}. Retrying...", icon="⚠️")
    return None

def find_and_update_node(tree, target_path, new_children):
    """Recursively finds a node by path and updates its children."""
    if tree.get('path') == target_path:
        tree['children'] = new_children
        return True
    
    for child in tree.get('children', []):
        if find_and_update_node(child, target_path, new_children):
            return True
    return False

def find_node_by_path(tree, path):
    """Finds and returns a node by its path."""
    if tree.get('path') == path:
        return tree
    for child in tree.get('children', []):
        found = find_node_by_path(child, path)
        if found:
            return found
    return None

def _collapse_nodes_recursively(node):
    """Sets collapsed flags on nodes based on UI interaction rules."""
    if not node.get('children'):
        return

    last_clicked_path = st.session_state.get("last_clicked_path")
    active_child_path = None

    # Check if any child is on the active path
    if last_clicked_path:
        for child in node['children']:
            if last_clicked_path.startswith(child.get('path', '')):
                active_child_path = child.get('path')
                break
    
    # Apply collapsing rules
    children_list = node['children']
    if active_child_path:
        # Collapse siblings of the clicked node
        for child in children_list:
            child['collapsed'] = (child.get('path') != active_child_path)
    elif len(children_list) > 4:
        # Collapse oldest nodes if more than 4
        for i, child in enumerate(children_list):
            child['collapsed'] = (i < len(children_list) - 4)
    else:
        # Default: nothing collapsed
        for child in children_list:
            child['collapsed'] = False

    # Recurse for all children
    for child in node['children']:
        _collapse_nodes_recursively(child)

def _apply_visual_formatting(node):
    """Applies display formatting based on collapsed state."""
    if node.get('collapsed'):
        node['name'] = "..."
    else:
        clean_desc = node.get('description', '').replace('\n', ' ')
        node['name'] = f"{node.get('name', '')}: {clean_desc}"
    
    # Color coding for different outcome types
    path = node.get('path', '')
    if path == '0' or path.startswith('0-'):
        node['itemStyle'] = {'color': "#2ecc71"}  # Green for best case
    elif path == '2' or path.startswith('2-'):
        node['itemStyle'] = {'color': "#e74c3c"}  # Red for worst case
    elif path == '1' or path.startswith('1-'):
        node['itemStyle'] = {'color': "#f39c12"}  # Orange for expected
    else:
        node['itemStyle'] = {'color': "#3498db"}  # Blue default
    
    if 'children' in node and node.get('children') is not None:
        for child in node['children']:
            _apply_visual_formatting(child)

def prepare_tree_for_display(node):
    """Prepares tree data for ECharts visualization."""
    _collapse_nodes_recursively(node)
    _apply_visual_formatting(node)

def create_echarts_tree_option(tree_data):
    """Creates ECharts tree visualization options."""
    return {
        "tooltip": {"trigger": 'item', "triggerOn": 'mousemove', "formatter": "{b}"},
        "series": [{
            "type": "tree",
            "data": [tree_data],
            "top": "5%", "left": "15%", "bottom": "5%", "right": "25%",
            "symbolSize": 15,
            "orient": "LR",
            "layout": "orthogonal",
            "expandAndCollapse": True,
            "initialTreeDepth": 10,
            "label": {
                "backgroundColor": 'rgba(0, 0, 0, 0.7)', "padding": [10, 14],
                "borderRadius": 8, "position": "right", "verticalAlign": "middle",
                "align": "left", "color": "#fff", "fontSize": 15,
                "width": 250,
                "overflow": "break"
            },
            "leaves": {"label": {"position": "right", "verticalAlign": "middle", "align": "left"}},
            "emphasis": {"focus": "descendant"},
            "animationDuration": 550, "animationDurationUpdate": 750,
        }]
    }

# --- Streamlit App UI ---
st.title("🧠 Overthinker Guide")
st.markdown("<p style='text-align: center;'>What situation are you overthinking? Let's break it down into possible outcomes.</p>", unsafe_allow_html=True)

# --- State Management ---
if 'current_tree' not in st.session_state:
    st.session_state.history = []
    st.session_state.current_tree = None
    st.session_state.user_scenario = ""
    st.session_state.last_clicked_path = None
    st.session_state.summary = ""

# --- UI Components ---
user_scenario_input = st.text_area(
    "Describe the situation you're overthinking:", 
    height=120, 
    placeholder="e.g., 'I have a job interview tomorrow and I'm worried I'll mess it up', 'I sent a message and they haven't replied yet'...", 
    label_visibility="visible"
)

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🔍 Analyze Outcomes", type="primary", use_container_width=True):
        if not user_scenario_input:
            st.warning("Please describe your situation first.", icon="✍️")
        else:
            with st.spinner("Analyzing possible outcomes..."):
                st.session_state.user_scenario = user_scenario_input
                prompt = PROMPT_INITIAL.format(user_scenario=st.session_state.user_scenario)
                ai_data = call_gemini_api(prompt)
                if ai_data and 'tree' in ai_data:
                    st.session_state.current_tree = ai_data['tree']
                    st.session_state.history = [copy.deepcopy(st.session_state.current_tree)]
                    st.session_state.summary = ai_data.get('summary', "")
                    st.session_state.last_clicked_path = None
                else:
                    st.error("Failed to generate analysis. Please try again.", icon="🕸️")
                    st.session_state.current_tree = None

with col2:
    if len(st.session_state.get('history', [])) > 1:
        if st.button("⬅️ Go Back", use_container_width=True):
            st.session_state.history.pop()
            st.session_state.current_tree = copy.deepcopy(st.session_state.history[-1])
            st.session_state.last_clicked_path = None
            st.rerun()

# --- Tree Display Logic ---
if st.session_state.current_tree:
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
    st.subheader("Outcome Tree")
    st.markdown("<p style='text-align: center; font-size: 0.9em; color: rgba(255,255,255,0.7);'>🟢 Best Case | 🟠 Expected | 🔴 Worst Case</p>", unsafe_allow_html=True)

    display_data = copy.deepcopy(st.session_state.current_tree)
    prepare_tree_for_display(display_data)
    options = create_echarts_tree_option(display_data)

    clicked_event = st_echarts(
        options=options, 
        height="600px", 
        key="tree_chart", 
        events={"click": "function(params) { if(params.data.path) { return params.data; } return null;}"}
    )

    if clicked_event and clicked_event.get("path"):
        clicked_path = clicked_event["path"]
        
        if clicked_path != st.session_state.last_clicked_path:
            st.session_state.last_clicked_path = clicked_path
            node_in_state = find_node_by_path(st.session_state.current_tree, clicked_path)
            
            if node_in_state and not node_in_state.get("children"):
                with st.spinner(f"Exploring '{node_in_state['name']}'..."):
                    prompt = PROMPT_EXPAND.format(
                        user_scenario=st.session_state.user_scenario,
                        path_name=node_in_state['name'],
                        path_description=node_in_state['description'],
                        parent_path=clicked_path
                    )
                    expanded_data = call_gemini_api(prompt)

                    if expanded_data and 'children' in expanded_data:
                        st.session_state.history.append(copy.deepcopy(st.session_state.current_tree))
                        find_and_update_node(st.session_state.current_tree, clicked_path, expanded_data['children'])
                        st.rerun()
                    else:
                        st.warning("Could not expand this outcome further.", icon="⚠️")

    st.markdown("<hr style='border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
    st.subheader("Perspective & Insight")
    summary_html = f'<div class="summary-box">{st.session_state.get("summary", "")}</div>'
    st.markdown(summary_html, unsafe_allow_html=True)
