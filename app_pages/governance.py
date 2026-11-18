import pandas as pd
import streamlit as st

from regqa import source, ui
from regqa.roles import LABEL, ROLES

st.caption("What each role can discover on the MCP server, and what it can actually call.")

ALL = ["regulation_search", "policy_search", "control_testing_analyst", "assess_gap", "open_remediation_ticket"]
listed = {r: {t["name"] for t in source.tools(r)} for r in ROLES}
grid = pd.DataFrame({LABEL[r]: ["Can call" if t in ROLES[r]["tools"] else ("Listed, call refused" if t in listed[r] else "Not listed")
                               for t in ALL] for r in ROLES}, index=[f"{t} · {ui.TOOL_KIND[t]}" for t in ALL])
st.dataframe(grid)
st.caption("tools/list returns every tool on this server to any role with USAGE on the server; each call is then checked "
           "against the role's grant on the underlying search service, semantic view, function or procedure. "
           "(Snowflake hides agent tools from roles without USAGE on the agent; other tool types are listed.)")

st.subheader("Business units each role can see", anchor=False)
st.dataframe(pd.DataFrame([{"Role": LABEL[r], "Snowflake role": r, "Business units": ", ".join(v["business_units"]) or "none"}
                           for r, v in ROLES.items()]), hide_index=True)

st.subheader("The grants behind it", anchor=False)
st.code("""-- Server access alone grants no tools
GRANT USAGE ON MCP SERVER REGQA_MCP TO ROLE REGQA_ANALYST;
GRANT USAGE ON MCP SERVER REGQA_MCP TO ROLE REGQA_COMPLIANCE_LEAD;
GRANT USAGE ON MCP SERVER REGQA_MCP TO ROLE REGQA_AUDITOR;

-- Each tool is granted on its own object
GRANT USAGE ON CORTEX SEARCH SERVICE REG_SEARCH TO ROLE REGQA_ANALYST;
GRANT SELECT ON SEMANTIC VIEW CONTROL_TESTS_SV TO ROLE REGQA_ANALYST;
GRANT USAGE ON FUNCTION ASSESS_GAP(STRING, STRING) TO ROLE REGQA_ANALYST;
GRANT USAGE ON PROCEDURE OPEN_REMEDIATION_TICKET(STRING, STRING, STRING, STRING)
  TO ROLE REGQA_COMPLIANCE_LEAD;                       -- the write tool: lead only

-- Data rules still apply to whatever a tool touches
ALTER TABLE CONTROL_TESTS ADD ROW ACCESS POLICY regqa_bu_policy ON (BUSINESS_UNIT);""", language="sql")

ui.snowflake_callout("Least privilege for MCP",
                     "Snowflake recommends a least-privileged role for every MCP client, OAuth over long-lived tokens, and "
                     "keeping SQL execution off servers meant for governed business questions. This server exposes no "
                     "SQL execution tool.")
