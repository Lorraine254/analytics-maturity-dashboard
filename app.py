import streamlit as st
import base64
from pathlib import Path
from streamlit_autorefresh import st_autorefresh


# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Analytics Maturity Dashboard",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>

/* =========================================
   TOP NAVIGATION
   ========================================= */

/* Navigation bar */
[data-testid="stHeader"] {
    background-color: #173F6B;
}

/* Navigation links */
[data-testid="stHeader"] a {
    color: white !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
}

/* Increase spacing between navigation items */
[data-testid="stHeader"] nav {
    gap: 60px !important;
}

/* Navigation text */
[data-testid="stHeader"] span {
    color: white !important;
}

/* Active navigation item */
[data-testid="stHeader"] a[aria-current="page"] {
    background-color: rgba(255, 255, 255, 0.18) !important;
    border-radius: 6px !important;
}

/* Keep header controls visible */
[data-testid="stHeader"] button {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Auto-refresh
# --------------------------------------------------
st_autorefresh(
    interval=5000,
    key="dashboard_refresh"
)


# --------------------------------------------------
# Background image
# --------------------------------------------------
def get_base64_image(image_path):
    image_path = Path(image_path)

    if not image_path.exists():
        return None

    with open(image_path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode()


background_image = get_base64_image(
    "assets/dashboard_background.png"
)


# --------------------------------------------------
# Global dashboard styling
# --------------------------------------------------
if background_image:

    background_css = f"""
    background-image:
        linear-gradient(
            rgba(255, 255, 255, 0.60),
            rgba(255, 255, 255, 0.60)
        ),
        url("data:image/png;base64,{background_image}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    """

else:

    background_css = """
    background-color: #EEF6FC;
    """


st.markdown(
    f"""
    <style>

    /* --------------------------------------------------
       Main application background
       -------------------------------------------------- */

    [data-testid="stAppViewContainer"] {{
        {background_css}
    }}

    [data-testid="stMain"] {{
        background: transparent;
    }}

    [data-testid="stMainBlockContainer"] {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}


    /* --------------------------------------------------
       Sidebar
       -------------------------------------------------- */

    [data-testid="stSidebar"] {{
        background: #203F68;
        border-right: 1px solid rgba(255, 255, 255, 0.15);
    }}

    [data-testid="stSidebar"] * {{
        color: #FFFFFF;
    }}

    [data-testid="stSidebar"] a {{
        color: #FFFFFF !important;
    }}

    [data-testid="stSidebarNav"] span {{
        color: #FFFFFF !important;
    }}


    /* Navigation section headings */
    [data-testid="stSidebar"] [data-testid="stNavSectionHeader"] {{
        color: #9CCDF5 !important;
        font-weight: 700;
    }}


    /* --------------------------------------------------
       Sidebar navigation links
       -------------------------------------------------- */

    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
        border-radius: 8px;
        margin-bottom: 3px;
    }}

    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
        background-color: rgba(255, 255, 255, 0.10);
    }}

    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {{
        background-color: #69B3F3;
    }}

    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] * {{
        color: #17375E !important;
        font-weight: 600;
    }}


    /* --------------------------------------------------
       Sidebar expander
       -------------------------------------------------- */

    [data-testid="stSidebar"] details {{
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 10px;
    }}


    /* --------------------------------------------------
       Main text
       -------------------------------------------------- */

    h1, h2, h3 {{
        color: #17375E;
    }}


    /* --------------------------------------------------
       KPI cards
       We use bordered Streamlit containers for KPI cards.
       -------------------------------------------------- */

    div[data-testid="stVerticalBlockBorderWrapper"]:has(
        div[data-testid="stMetric"]
    ) {{
        background: rgba(132, 193, 242, 0.88);
        border: none !important;
        border-radius: 10px;
        box-shadow: 0 2px 7px rgba(31, 63, 104, 0.10);
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(
        div[data-testid="stMetric"]
    ) div[data-testid="stMetric"] {{
        padding: 0.35rem 0.45rem;
    }}

    div[data-testid="stMetricLabel"] {{
        color: #17375E;
        font-weight: 500;
    }}

    div[data-testid="stMetricValue"] {{
        color: #17375E;
        font-weight: 600;
    }}


    /* --------------------------------------------------
       Chart cards
       -------------------------------------------------- */

    div[data-testid="stVerticalBlockBorderWrapper"]:has(
        div[data-testid="stPlotlyChart"]
    ) {{
        background: rgba(255, 255, 255, 0.90);
        border: 1px solid rgba(31, 63, 104, 0.70) !important;
        border-radius: 14px;
        box-shadow: 0 3px 10px rgba(31, 63, 104, 0.08);
        padding: 0.35rem;
    }}


    /* --------------------------------------------------
       Segmented control
       -------------------------------------------------- */

    [data-testid="stSegmentedControl"] {{
        background: transparent;
    }}


    /* --------------------------------------------------
       Divider
       -------------------------------------------------- */

    [data-testid="stSidebar"] hr {{
        border-color: rgba(255, 255, 255, 0.25);
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# Navigation
# --------------------------------------------------
pages = [
    st.Page(
        "overview.py",
        title="Overview",
        icon=":material/dashboard:"
    ),

    st.Page(
        "pages/1_Business_Decisions_Analytics.py",
        title="Business Decisions & Analytics"
    ),

    st.Page(
        "pages/2_Data_Information.py",
        title="Data & Information"
    ),

    st.Page(
        "pages/3_Technology_Infrastructure.py",
        title="Technology & Infrastructure"
    ),

    st.Page(
        "pages/4_Process_Integration.py",
        title="Process & Integration"
    ),

    st.Page(
        "pages/5_Organization_Governance.py",
        title="Organization & Governance"
    )
]

navigation = st.navigation(
    pages,
    position="top"
)

navigation.run()

# --------------------------------------------------
# Score interpretation
# --------------------------------------------------

with st.sidebar:

    st.title("Analytics Maturity Dashboard")

    st.divider()

    st.subheader("How to interpret the scores")

    st.markdown("""
    **Maturity Scale**

    - **1 — Limited**
    - **2 — Evolving**
    - **3 — Acceptable**
    - **4 — Advanced**
    - **5 — Optimizing**

    - Higher scores indicate greater analytics maturity.

    - **Current State** reflects the organization's present analytics maturity, while **Future State** reflects its desired maturity.

    - **Industry Benchmark** compares the assessment against benchmark companies in the **Banking and Capital Markets sector**. 
    """)