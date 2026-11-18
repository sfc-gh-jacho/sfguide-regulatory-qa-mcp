import streamlit as st

from regqa import source, ui

st.caption("Every JSON-RPC message this app exchanged with the MCP server, newest first. "
           "This is exactly what any MCP client sends and receives.")

c = source.client()
st.code(f"POST {c.url}\nAuthorization: Snowflake Token=\"…\"   (OAuth or a programmatic access token for other clients)\n"
        "Accept: application/json, text/event-stream", language="http")

tr = source.trace()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Calls", len(tr), border=True)
c2.metric("Refused", sum(not e["ok"] for e in tr), border=True)
c3.metric("Bytes returned", f"{sum(e['bytes'] for e in tr):,}", border=True)
c4.metric("Slowest call", f"{max((e['ms'] for e in tr), default=0):,} ms", border=True)

methods = sorted({e["method"] for e in tr})
tools = sorted({e["tool"] for e in tr if e["tool"]})
f1, f2 = st.columns(2)
m = f1.multiselect("Method", methods, default=methods)
t = f2.multiselect("Tool", tools, default=tools)
shown = [e for e in reversed(tr) if e["method"] in m and (not e["tool"] or e["tool"] in t)]
if not shown:
    st.info("No calls yet. Ask a question on page 1.", icon=":material/forum:")
for i, e in enumerate(shown[:60]):
    ui.call_card(e, expanded=i == 0)

with st.expander("How to read this", icon=":material/help:"):
    st.markdown(
        "- `initialize` opens the session and agrees the protocol version.\n"
        "- `tools/list` is discovery: the server returns each tool's name, description, input schema and annotations.\n"
        "- `tools/call` runs one tool. Search tools return ranked rows, Cortex Analyst returns SQL, custom tools return "
        "whatever the UDF or procedure returns.\n"
        "- Tool results stream back as Server-Sent Events; the app reads the final `data:` event.\n"
        "- A refused call still returns HTTP 200 with `isError: true`. The refusal comes from Snowflake access control, "
        "not from the app.")
