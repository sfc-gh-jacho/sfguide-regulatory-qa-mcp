"""Shared UI pieces."""

from __future__ import annotations

import json

import streamlit as st

TOOL_ICON = {"regulation_search": ":material/gavel:", "policy_search": ":material/policy:",
             "control_testing_analyst": ":material/query_stats:", "assess_gap": ":material/compare_arrows:",
             "open_remediation_ticket": ":material/assignment_add:"}
TOOL_KIND = {"regulation_search": "Cortex Search", "policy_search": "Cortex Search",
             "control_testing_analyst": "Cortex Analyst", "assess_gap": "Custom UDF (AI_COMPLETE)",
             "open_remediation_ticket": "Custom stored procedure"}


def snowflake_callout(title: str, body: str) -> None:
    with st.container(border=True):
        st.markdown(f":blue[:material/ac_unit:] **Powered by Snowflake: {title}**")
        st.caption(body)


def source_badge(live: bool) -> None:
    if live:
        st.badge("Live call to the MCP server", icon=":material/bolt:", color="violet")
    else:
        st.badge("Replay of a captured MCP call", icon=":material/history:", color="gray")


def verdict_badge(v: str | None) -> None:
    if v == "GAP":
        st.badge("Gap", icon=":material/error:", color="red")
    elif v == "MEETS":
        st.badge("Meets", icon=":material/check_circle:", color="green")
    elif v:
        st.badge("Not related", icon=":material/help:", color="gray")


def pretty(obj, limit: int = 6000) -> str:
    s = json.dumps(obj, indent=2, ensure_ascii=False)
    return s if len(s) <= limit else s[:limit] + "\n… (truncated for display)"


def call_card(e: dict, expanded: bool = False) -> None:
    """One JSON-RPC exchange, as it crossed the wire."""
    tool = e.get("tool") or ""
    status = ":green[OK]" if e["ok"] else ":red[REFUSED]"
    title = f"#{e['id']} · `{e['method']}`" + (f" · `{tool}`" if tool else "") + f" · {status} · {e['ms']} ms · {e['bytes']:,} bytes"
    with st.expander(title, expanded=expanded, icon=TOOL_ICON.get(tool, ":material/swap_horiz:")):
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"Request · POST · role {e['role']}")
            st.code(pretty(e["request"]), language="json")
        with c2:
            st.caption(f"Response · HTTP {e['http']} · {e['content_type']}")
            st.code(pretty(e["response"]), language="json")
