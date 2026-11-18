import json

import pandas as pd
import streamlit as st

from regqa import source, ui

st.caption("Tool results leave Snowflake. Whatever a tool returns goes to the MCP client and, through the client, to "
           "any model provider it uses. This page shows exactly what left, call by call.")

tr = source.trace()
calls = [e for e in tr if e["method"] == "tools/call"]
if not calls:
    st.info("No tool calls yet. Ask a question on page 1.", icon=":material/forum:")
else:
    rows = []
    for e in calls:
        txt = json.dumps(e["response"].get("result", {}), ensure_ascii=False)
        rows.append({"#": e["id"], "Time": e["ts"], "Role": e["role"], "Tool": e["tool"], "Status": "OK" if e["ok"] else "REFUSED",
                     "Bytes out": e["bytes"], "Contains": ", ".join(k for k in ("CLAUSE_ID", "SECTION_ID", "OWNER", "statement", "verdict", "Opened")
                                                                    if k in txt) or "error text"})
    df = pd.DataFrame(rows)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tool calls", len(df), border=True)
    c2.metric("Bytes that left Snowflake", f"{int(df['Bytes out'].sum()):,}", border=True)
    c3.metric("Refused calls", int((df.Status == "REFUSED").sum()), border=True, help="Refusals return only an error message, no data.")
    st.dataframe(df, hide_index=True)
    pick = st.selectbox("Inspect one payload", [e["id"] for e in calls][::-1], format_func=lambda i: f"Call #{i}")
    e = next(x for x in calls if x["id"] == pick)
    st.code(ui.pretty(e["response"]), language="json")

st.subheader("Audit log in Snowflake", anchor=False)
if source.is_live():
    try:
        log = source.live_table("SELECT EVENT_TS, SESSION_ID, ROLE_NAME, METHOD, TOOL, STATUS, LATENCY_MS, RESULT_BYTES "
                                "FROM REGQA_DEMO_DB.DESK.MCP_AUDIT ORDER BY EVENT_TS DESC LIMIT 200", source.role())
        st.dataframe(log, hide_index=True)
        st.caption("The app appends every call it makes to MCP_AUDIT. Analysts can write to it but not read it.")
    except Exception:
        st.warning("This role can append to MCP_AUDIT but cannot read it.", icon=":material/visibility_off:")
else:
    st.caption("In live mode, the app appends every call to the MCP_AUDIT table, and internal audit reads it here. "
               "Snowflake's own query history also records the SQL each tool ran.")

ui.snowflake_callout("Decide what each tool may return before you expose it",
                     "A tool returns only what the calling role can read. Here the search tools return clause and policy "
                     "text, Cortex Analyst returns SQL (the client runs it under its own role), and refused calls return "
                     "nothing but an error message.")
