import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Analytics Maturity Dashboard",
    page_icon="📊",
    layout="wide"
)

# Refresh the active dashboard page every 5 seconds
st_autorefresh(
    interval=5000,
    key="dashboard_refresh"
)

# --------------------------------------------------
# Navigation
# --------------------------------------------------
pages = {
    "Dashboard": [
        st.Page(
            "overview.py",
            title="Overview",
            icon=":material/dashboard:"
        )
    ],

    "Dimensions": [
        st.Page(
            "pages/1_Business_Decisions_Analytics.py",
            title="Business Decisions & Analytics",
            icon=":material/analytics:"
        ),
        st.Page(
            "pages/2_Data_Information.py",
            title="Data & Information",
            icon=":material/database:"
        ),
        st.Page(
            "pages/3_Technology_Infrastructure.py",
            title="Technology & Infrastructure",
            icon=":material/memory:"
        ),
        st.Page(
            "pages/4_Process_Integration.py",
            title="Process & Integration",
            icon=":material/account_tree:"
        ),
        st.Page(
            "pages/5_Organization_Governance.py",
            title="Organization & Governance",
            icon=":material/group:"
        )
    ]
}


navigation = st.navigation(
    pages,
    position="sidebar"
)

navigation.run()


with st.sidebar.expander("How to interpret the scores"):
    st.markdown(
        """
        **Maturity Scale**

        - **1 — Limited**
        - **2 — Evolving**
        - **3 — Acceptable**
        - **4 — Advanced**
        - **5 — Optimizing**

        Each response is weighted according to its assessment question. 
        The weighted contributions are combined to calculate the dimension 
        and overall maturity scores.

        **Higher scores indicate greater analytics maturity.**
        """
    )