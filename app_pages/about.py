import streamlit as st

from regqa import data

st.markdown(f"""
This example shows a compliance desk built on a **Snowflake-managed MCP server**. Everything is synthetic: the
{data.REGULATOR}, {data.BANK}, its policies, owners and control test results are invented.

**What runs where**
- **Snowflake:** two Cortex Search services, a semantic view for Cortex Analyst, a gap-assessment UDF that calls
  `AI_COMPLETE`, a ticket procedure, one MCP server that exposes all five, three roles, and a row access policy.
- **This app:** an MCP client. It follows a fixed, visible playbook (search regulations, search policies, assess the
  best pair, or ask Cortex Analyst) and assembles the answer from tool results only.
- **Captured replay:** in sample mode, responses come from a file recorded from the real server with
  `scripts/capture.py`, so the app runs in a browser with no account.
""")

st.subheader("Connect another MCP client", anchor=False)
st.markdown("Any MCP client can use the same server. For Claude or Cursor, create an OAuth security integration "
            "(see the README), set your user's default role to one of the REGQA_ roles, and add the server URL:")
st.code("""{
  "mcpServers": {
    "regqa-desk": {
      "url": "https://<account-url-with-hyphens>/api/v2/databases/REGQA_DEMO_DB/schemas/DESK/mcp-servers/REGQA_MCP"
    }
  }
}""", language="json")
st.caption("Use hyphens, not underscores, in the account host name. Tool results go to the client and its model provider.")

st.subheader("Known limitations", anchor=False)
st.markdown("""
- Sample mode can replay only the scripted questions and roles it captured.
- The playbook is simple on purpose. A production desk would usually expose a Cortex Agent as the single MCP tool and let
  it orchestrate the others.
- The gap tool is an LLM judgement. It matched all 34 test pairs in testing, but a reviewer should confirm every gap.
- Cortex Analyst needs specific models to be available and granted in your region (see the README).
""")

if st.button("Reset this session", icon=":material/restart_alt:"):
    for k in ("trace", "results", "findings", "tickets", "last_ticket", "initialized"):
        st.session_state.pop(k, None)
    st.rerun()
st.caption("**Owner:** Janet Cho · **Last reviewed:** November 2026 · Apache 2.0")
