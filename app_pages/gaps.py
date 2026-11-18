import pandas as pd
import streamlit as st

from regqa import desk, mcp, source, ui
from regqa.roles import LABEL, ROLES

st.caption("Gaps found on the Ask page, and remediation tickets. Opening a ticket writes to Snowflake, so a person "
           "approves each call first, and only roles granted the ticket tool can make it.")

findings = st.session_state.setdefault("findings", {})
gaps = [f for f in findings.values() if f["verdict"] == "GAP"]

with st.container(horizontal=True):
    if st.button("Check all scripted topics", icon=":material/playlist_add_check:",
                 help="Runs the six policy questions from page 1 as the current role."):
        before = len(source.trace())
        bar = st.progress(0.0, text="Calling MCP tools...")
        qs = [q for q in desk.QUESTIONS if not desk.NUMERIC.search(q[1])]
        for i, (_, q) in enumerate(qs):
            res = desk.ask(source.client(), q, source.run_sql_for(source.role()))
            f = desk.finding(res)
            if f:
                findings[f["section"]["SECTION_ID"]] = f
            bar.progress((i + 1) / len(qs), text=q[:70])
        source.log_audit(source.trace()[before:])
        st.rerun()

if not findings:
    st.info("No findings yet. Ask a question, or check all scripted topics.", icon=":material/search:")
else:
    rows = [{"Verdict": f["verdict"], "Policy section": f["section"]["SECTION_ID"], "Policy": f["section"]["POLICY_TITLE"],
             "Regulation clause": f["clause"]["CLAUSE_ID"], "Regulation requires": f.get("regulation_requires", ""),
             "Policy says": f.get("policy_says", "")} for f in findings.values()]
    st.dataframe(pd.DataFrame(rows).sort_values("Verdict"), hide_index=True)

st.subheader("Approve a remediation ticket", anchor=False)
if not gaps:
    st.caption("Gaps you find will appear here for approval.")
else:
    f = st.selectbox("Gap", gaps, format_func=lambda g: f"{g['section']['SECTION_ID']} vs {g['clause']['CLAUSE_ID']}: {g['section']['POLICY_TITLE']}")
    args = desk.proposed_ticket(f)
    allowed = "open_remediation_ticket" in ROLES[source.role()]["tools"]
    with st.container(border=True):
        st.markdown(":material/assignment_add: **Proposed tool call** · `open_remediation_ticket`")
        st.caption("Annotations from tools/list: readOnlyHint false, destructiveHint false. Annotations are hints for the "
                   "client; the grant on the procedure is the actual control.")
        st.code(ui.pretty({"name": "open_remediation_ticket", "arguments": args}), language="json")
        if not allowed:
            st.caption(f":material/info: {LABEL[source.role()]} is not granted this tool. You can still approve the call "
                       "to see Snowflake refuse it.")
        if st.button("Approve and call the tool", type="primary", icon=":material/check:"):
            before = len(source.trace())
            r = source.client().call("open_remediation_ticket", args)
            source.log_audit(source.trace()[before:])
            msg = mcp.text_of(r)
            if r.get("isError"):
                st.session_state.last_ticket = ("error", desk.error_of(r) or msg[:240])
            else:
                st.session_state.last_ticket = ("ok", msg)
                if not source.is_live():
                    st.session_state.setdefault("tickets", []).insert(0, {
                        "TICKET_ID": msg.split()[1] if msg.startswith("Opened") else "", "OPENED_ROLE": source.role(),
                        "POLICY_SECTION_ID": args["section_id"], "CLAUSE_ID": args["clause_id"], "SEVERITY": args["severity"],
                        "SUMMARY": args["summary"], "STATUS": "OPEN", "WRITTEN_TO": "This browser session (replay)"})
                else:
                    source.live_table.clear()
            st.rerun()
    if "last_ticket" in st.session_state:
        kind, msg = st.session_state.last_ticket
        (st.success if kind == "ok" else st.error)(msg, icon=":material/check_circle:" if kind == "ok" else ":material/block:")

st.subheader("Remediation tickets", anchor=False)
t = source.tickets()
if t.empty:
    st.caption("No tickets yet." if ROLES[source.role()]["tools"] or source.is_live() else "This role cannot read tickets.")
else:
    st.dataframe(t, hide_index=True)

ui.snowflake_callout("Custom tools with human approval",
                     "The ticket tool is a SQL stored procedure exposed through the MCP server. It runs with the caller's rights, "
                     "so it writes as the role that called it, and only REGQA_COMPLIANCE_LEAD holds USAGE on it.")
