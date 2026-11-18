import pandas as pd
import streamlit as st

from regqa import desk, source, ui
from regqa.roles import LABEL

st.caption("Ask a compliance question. The app is an MCP client: it calls tools on the Snowflake-managed MCP server "
           "as the role in the sidebar and builds the answer only from what those tools return.")

replay = not source.is_live()
labels = {q: q for _, q in desk.QUESTIONS}
pick = st.pills("Try a question", list(labels), selection_mode="single", key="pick")
free = None
if source.is_live():
    free = st.chat_input("Or ask your own question")
else:
    st.caption(":material/info: Captured replay answers the questions above. Connect to Snowflake to ask anything.")
question = free or pick

results = st.session_state.setdefault("results", {})
if question:
    rk = (question, source.role(), source.is_live())
    if rk not in results:
        before = len(source.trace())
        with st.status(f"Calling MCP tools as {LABEL[source.role()]}...", expanded=True) as s:
            res = desk.ask(source.client(), question, source.run_sql_for(source.role()))
            for stp in res["steps"]:
                icon = ":green[:material/check_circle:]" if stp["ok"] else ":red[:material/block:]"
                st.markdown(f"{icon} {stp['label']} · `{stp['tool']}`" + (f" · {stp['error']}" if stp["error"] else ""))
            s.update(label="Done" if not res["errors"] else "Done, with refused calls", state="complete" if not res["errors"] else "error",
                     expanded=False)
        res["calls"] = [e["id"] for e in source.trace()[before:]]
        source.log_audit(source.trace()[before:])
        results[rk] = res
        f = desk.finding(res)
        if f:
            st.session_state.setdefault("findings", {})[f["section"]["SECTION_ID"]] = f
    res = results[rk]

    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant", avatar=":material/gavel:"):
        ui.source_badge(source.is_live())
        f = desk.finding(res)
        if f:
            ui.verdict_badge(f["verdict"])
        st.markdown(desk.answer_md(res))
        a = res.get("analyst")
        if a:
            if a.get("rows"):
                df = pd.DataFrame(a["rows"], columns=a["columns"])
                for c in df.columns:
                    if "RATE" in c.upper():
                        df[c] = pd.to_numeric(df[c])
                st.dataframe(df, hide_index=True, column_config={c: st.column_config.NumberColumn(format="percent")
                                                                 for c in df.columns if "RATE" in c.upper()})
                st.caption(f"Rows returned to {LABEL[source.role()]}: the row access policy on CONTROL_TESTS decides which business units appear.")
            if a.get("sql"):
                with st.expander("SQL written by Cortex Analyst", icon=":material/code:"):
                    st.code(a["sql"], language="sql")
        if f:
            c1, c2 = st.columns(2)
            with c1, st.container(border=True):
                st.markdown(f":material/gavel: **{f['clause']['CLAUSE_ID']}** · {f['clause']['REGULATION_TITLE']}")
                st.caption(f['clause']['HEADING'])
                st.write(f['clause']['TEXT'])
            with c2, st.container(border=True):
                st.markdown(f":material/policy: **{f['section']['SECTION_ID']}** · {f['section']['POLICY_TITLE']}")
                st.caption(f"{f['section']['HEADING']} · owner: {f['section'].get('OWNER', '')}")
                st.write(f['section']['TEXT'])
            if f["verdict"] == "GAP":
                st.page_link("app_pages/gaps.py", label="Propose a remediation ticket for this gap", icon=":material/assignment_add:")
        if res["errors"]:
            st.warning("Snowflake refused " + ", ".join(sorted({e.split(':')[0] for e in res['errors']}))
                       + f" for {LABEL[source.role()]}. The role can reach the MCP server but was not granted these tools.",
                       icon=":material/block:")
        st.page_link("app_pages/inspector.py", label=f"See the {len(res['calls'])} JSON-RPC calls behind this answer",
                     icon=":material/data_object:")

ui.snowflake_callout("Snowflake-managed MCP server",
                     "One CREATE MCP SERVER statement exposes two Cortex Search services, a Cortex Analyst semantic view, "
                     "a gap-assessment UDF and a ticket procedure as MCP tools. Any MCP client (this app, Claude, Cursor) "
                     "calls the same tools, and Snowflake checks the caller's role on every call.")
