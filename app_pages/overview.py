import pandas as pd
import streamlit as st

from regqa import data, source, ui

st.markdown(f"A compliance team at **{data.BANK}** checks its internal policies against rules from the "
            f"**{data.REGULATOR}**. Instead of building a custom integration, the bank exposes its Snowflake data "
            "and AI services as tools on one **Snowflake-managed MCP server**. Any MCP client can use them, and "
            "Snowflake checks the caller's role on every call.")

t = source.tables()
c = st.columns(5)
c[0].metric("Regulations", len(t["REGULATIONS"]), border=True)
c[1].metric("Regulation clauses", len(t["REG_CLAUSES"]), border=True)
c[2].metric("Policy sections", len(t["POLICY_SECTIONS"]), border=True, help=f"{len(t['POLICIES'])} policies")
c[3].metric("Controls", len(t["CONTROLS"]), border=True)
c[4].metric("Control tests", len(t["CONTROL_TESTS"]), border=True, help="4 quarters × 3 business units")
st.caption(f"About {len(data.GAPS)} of {len(data.REQUIREMENTS)} mapped requirements are planted gaps; the rest are met. "
           "All counts describe the synthetic dataset.")

st.subheader("How it works", anchor=False)
st.graphviz_chart("""
digraph {
  rankdir=LR; bgcolor="transparent"; node [shape=box style="rounded,filled" fontname="Inter" fontsize=11 color="#d0e8f2" fillcolor="#f4f9fc" fontcolor="#11567F"];
  edge [color="#29B5E8" fontname="Inter" fontsize=9 fontcolor="#5B7083"];
  subgraph cluster_c { label="MCP clients"; fontname="Inter"; fontcolor="#5B7083"; color="#d0e8f2"; app [label="This app"]; claude [label="Claude / Cursor\\n(optional)"]; }
  mcp [label="REGQA_MCP\\nSnowflake-managed\\nMCP server" fillcolor="#29B5E8" fontcolor="white" color="#29B5E8"];
  rs [label="regulation_search\\nCortex Search"]; ps [label="policy_search\\nCortex Search"];
  an [label="control_testing_analyst\\nCortex Analyst"]; ag [label="assess_gap\\nUDF + AI_COMPLETE"]; tk [label="open_remediation_ticket\\nstored procedure\\n(compliance lead only)"];
  app -> mcp [label="JSON-RPC over HTTPS"]; claude -> mcp [style=dashed];
  mcp -> rs; mcp -> ps; mcp -> an; mcp -> ag; mcp -> tk;
}
""")

st.subheader("Try it in three steps", anchor=False)
s1, s2, s3 = st.columns(3)
with s1, st.container(border=True):
    st.markdown("**1 · Ask a question**")
    st.caption("Pick a scripted question. Watch the desk search regulations and policies, then ask a gap tool for a verdict.")
    st.page_link("app_pages/ask.py", label="Ask the desk", icon=":material/forum:")
with s2, st.container(border=True):
    st.markdown("**2 · Open the inspector**")
    st.caption("See every JSON-RPC request and response, with timing and size. This is the MCP protocol itself.")
    st.page_link("app_pages/inspector.py", label="MCP inspector", icon=":material/data_object:")
with s3, st.container(border=True):
    st.markdown("**3 · Switch roles**")
    st.caption("Change 'Acting as' in the sidebar. The analyst cannot open tickets; the auditor cannot call any tool.")
    st.page_link("app_pages/governance.py", label="Roles and tool grants", icon=":material/shield_lock:")

st.subheader("What the data looks like", anchor=False)
st.caption("Six synthetic tables in REGQA_DEMO_DB.DESK, generated from one seed. Two more tables record what the app does. "
           "Every row below comes from the same data the MCP tools search and query.")

st.graphviz_chart("""
digraph {
  rankdir=TB; bgcolor="transparent"; nodesep=0.35; ranksep=0.45;
  node [shape=box style="rounded,filled" fontname="Inter" fontsize=12 color="#d0e8f2" fillcolor="#f4f9fc" fontcolor="#11567F" margin="0.18,0.08"];
  edge [color="#29B5E8" fontname="Inter" fontsize=10 fontcolor="#5B7083" arrowsize=.7];
  R  [label="REGULATIONS (12)\nrule, title, effective date"];
  P  [label="POLICIES (20)\npolicy, title, owner"];
  RC [label="REG_CLAUSES (160)\nclause text  →  regulation_search" fillcolor="#e8f4f8"];
  PS [label="POLICY_SECTIONS (180)\nsection text  →  policy_search" fillcolor="#e8f4f8"];
  C  [label="CONTROLS (50)\nmaps a clause to a policy section"];
  T  [label="CONTROL_TESTS (600)\nunit, quarter, PASS/FAIL  →  control_testing_analyst" fillcolor="#e8f4f8"];
  K  [label="REMEDIATION_TICKETS\nwritten by open_remediation_ticket" fillcolor="#FFF4E5"];
  A  [label="MCP_AUDIT\nevery call this app makes" fillcolor="#FFF4E5"];
  R -> RC; P -> PS; RC -> C; PS -> C; C -> T [label=" 4 quarters × 3 units"];
  RC -> K [style=dashed label=" cites"]; PS -> K [style=dashed];
  { rank=same; K; A; }
  T -> A [style=invis];
}
""")
st.caption("Blue tables back the tools: REG_CLAUSES feeds regulation_search, POLICY_SECTIONS feeds policy_search, and "
           "CONTROL_TESTS (through the CONTROL_TESTS_SV semantic view) feeds control_testing_analyst. assess_gap reads one "
           "clause and one section. Orange tables are written while you use the app.")

tabs = st.tabs(["Regulation clauses", "Policy sections", "Controls", "Control tests", "Planted gaps", "Regulations and policies"])
key_clauses = ["NFCA-R01 §4.2", "NFCA-R03 §2.1", "NFCA-R02 §3.4", "NFCA-R02 §3.6"]
key_sections = ["POL-07 §4", "POL-11 §3", "POL-05 §3", "POL-05 §4"]
with tabs[0]:
    st.caption("160 clauses across 12 rules. Each rule has boilerplate (purpose, scope, definitions), concrete requirements, "
               "and evidence clauses. These are four of the concrete requirements.")
    rc = t["REG_CLAUSES"]
    st.dataframe(rc[rc.CLAUSE_ID.isin(key_clauses)][["CLAUSE_ID", "REGULATION_TITLE", "HEADING", "TEXT", "EFFECTIVE_DATE"]],
                 hide_index=True, column_config={"TEXT": st.column_config.TextColumn(width="large")})
with tabs[1]:
    st.caption("180 sections across 20 policies, each with a named owner. These sections implement the clauses on the "
               "previous tab; compare the deadlines and frequencies.")
    ps = t["POLICY_SECTIONS"]
    st.dataframe(ps[ps.SECTION_ID.isin(key_sections)][["SECTION_ID", "POLICY_TITLE", "HEADING", "TEXT", "OWNER"]],
                 hide_index=True, column_config={"TEXT": st.column_config.TextColumn(width="large")})
with tabs[2]:
    st.caption("50 controls. 32 map a regulation clause to the policy section that implements it; 18 are general "
               "controls with no single clause.")
    st.dataframe(t["CONTROLS"].head(8), hide_index=True)
with tabs[3]:
    st.caption("600 test results: each control is tested every quarter (2025-Q4 to 2026-Q3) in each of three business "
               "units. A test samples items and records exceptions. These are the incident-notification control's results.")
    ct = t["CONTROL_TESTS"]
    st.dataframe(ct[ct.CONTROL_ID == "CTL-001"][["TEST_ID", "CONTROL_NAME", "BUSINESS_UNIT", "QUARTER", "OWNER",
                                                   "SAMPLE_SIZE", "EXCEPTIONS", "RESULT"]], hide_index=True)
with tabs[4]:
    st.caption("The answer key. Five policy sections were written to fall short of a regulation; the other 27 mapped "
               "requirements are met. The controls tied to these five fail far more often in testing.")
    gaps = pd.DataFrame([{"Policy section": f"{g[4]} §{g[5]}", "Regulation clause": f"{g[1]} §{g[2]}",
                          "Regulation requires": g[3], "Policy says": g[6]} for g in data.GAPS.values()])
    st.dataframe(gaps, hide_index=True, column_config={"Regulation requires": st.column_config.TextColumn(width="large"),
                                                         "Policy says": st.column_config.TextColumn(width="large")})
with tabs[5]:
    c1, c2 = st.columns(2)
    c1.dataframe(t["REGULATIONS"][["REGULATION_ID", "TITLE", "EFFECTIVE_DATE"]], hide_index=True)
    c2.dataframe(t["POLICIES"][["POLICY_ID", "TITLE", "OWNER"]], hide_index=True)

ui.snowflake_callout("Governed by the platform, not the client",
                     "Access to the MCP server does not give access to its tools. Each tool needs its own grant, row access "
                     "policies still apply to the data, and tool results go only where the calling role is allowed to see them.")
