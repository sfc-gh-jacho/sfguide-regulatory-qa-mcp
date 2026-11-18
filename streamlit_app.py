import uuid

import streamlit as st

from regqa import source
from regqa.roles import LABEL, ROLE_OF, ROLES

st.set_page_config(page_title="Regulatory Q&A desk", page_icon=":material/gavel:", layout="wide")

st.session_state.setdefault("mode", "live" if source.live_status() == "ready" else "sample")
st.session_state.setdefault("role", "REGQA_COMPLIANCE_LEAD")
st.session_state.setdefault("sid", ("sis-" if source.IN_SIS else "local-") + str(uuid.uuid4())[:8])

page = st.navigation(
    {
        "": [st.Page("app_pages/overview.py", title="Overview", icon=":material/dashboard:", default=True)],
        "Ask": [
            st.Page("app_pages/ask.py", title="1 · Ask the desk", icon=":material/forum:"),
            st.Page("app_pages/inspector.py", title="2 · MCP inspector", icon=":material/data_object:"),
        ],
        "Act": [
            st.Page("app_pages/gaps.py", title="3 · Gaps and approvals", icon=":material/assignment_late:"),
            st.Page("app_pages/controls.py", title="4 · Control testing", icon=":material/query_stats:"),
        ],
        "Trust": [
            st.Page("app_pages/audit.py", title="Audit: what left Snowflake", icon=":material/policy:"),
            st.Page("app_pages/governance.py", title="Roles and tool grants", icon=":material/shield_lock:"),
            st.Page("app_pages/about.py", title="About this example", icon=":material/info:"),
        ],
    }
)

with st.sidebar:
    st.markdown("**Regulatory Q&A desk**")
    if source.live_status() == "unavailable":
        st.badge("Sample mode", icon=":material/science:", color="blue")
        st.caption("No Snowflake account needed. Responses were captured from the real MCP server."
                   + (" Running entirely in your browser; nothing leaves this page." if source.IN_BROWSER else ""))
    else:
        choice = st.segmented_control("MCP server", ["Captured replay", "Live Snowflake"],
                                      default="Live Snowflake" if source.is_live() else "Captured replay", required=True)
        st.session_state.mode = "live" if choice == "Live Snowflake" else "sample"
    label = st.selectbox("Acting as", list(ROLE_OF), index=list(ROLE_OF).index(LABEL[st.session_state.role]),
                         help="Each role is a Snowflake role with its own tool grants. Switch to see what changes.")
    st.session_state.role = ROLE_OF[label]
    st.caption(ROLES[st.session_state.role]["blurb"])
    if st.session_state.mode == "live" and st.session_state.role not in source.live_roles():
        st.caption(f":material/history: This app runs as {', '.join(source.live_roles())} in Snowflake, so "
                   f"{label} is shown from its captured replay.")
    st.caption("The regulator, the bank, its policies and its test results are all fictional.")

with st.container(horizontal=True, vertical_alignment="center"):
    st.title(page.title, icon=page.icon, width="content", anchor=False)
    st.space("small")
    if source.is_live():
        st.badge("Live MCP server", icon=":material/ac_unit:", color="blue")
    else:
        st.badge("Captured replay", icon=":material/history:", color="gray")
    st.badge(LABEL[st.session_state.role], icon=":material/badge:", color="violet")
    st.badge("Synthetic data", icon=":material/lab_profile:", color="orange")

page.run()
