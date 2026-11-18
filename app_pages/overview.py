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

ui.snowflake_callout("Governed by the platform, not the client",
                     "Access to the MCP server does not give access to its tools. Each tool needs its own grant, row access "
                     "policies still apply to the data, and tool results go only where the calling role is allowed to see them.")
