"""Where the app gets its MCP client and data: captured replay, or live Snowflake.

Sample mode replays responses captured from the real REGQA_MCP server and needs
no account; it is the only mode in the browser (stlite). Live mode calls the MCP
server over HTTPS as the role picked in the sidebar. Running locally, it opens a
connector session per role, so your user needs the three REGQA_ roles.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from regqa import data, mcp
from regqa.roles import ROLES

IN_BROWSER = sys.platform == "emscripten"
# Streamlit in Snowflake (container runtime) provides a session token file; the app runs as its owner's role.
IN_SIS = os.path.exists("/snowflake/session/token")
DB = "REGQA_DEMO_DB.DESK"
ROOT = Path(__file__).resolve().parents[1]
CONNECTION = os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME")


@st.cache_data(show_spinner=False)
def captured() -> dict:
    return json.loads((ROOT / "data" / "captured_mcp.json").read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def sis_role() -> str | None:
    if not IN_SIS:
        return None
    return st.connection("snowflake").raw_connection.cursor().execute("SELECT CURRENT_ROLE()").fetchone()[0]


def live_roles() -> list[str]:
    """Roles this deployment can call the live server as. Locally: all three. In SiS: the app owner's role."""
    if IN_SIS:
        return [r for r in ROLES if r == sis_role()]
    return list(ROLES)


@st.cache_resource(show_spinner="Connecting to Snowflake...")
def _conn(role: str):
    if IN_SIS:
        return st.connection("snowflake").raw_connection
    import snowflake.connector

    kw = {"connection_name": CONNECTION} if CONNECTION else {}
    c = snowflake.connector.connect(role=role, warehouse="REGQA_WH", **kw)
    # Only this role's privileges count, so each role is tested on its own grants.
    c.cursor().execute("USE SECONDARY ROLES NONE")
    return c


@st.cache_data(ttl=300, show_spinner=False)
def live_status() -> str:
    """'unavailable' or 'ready'."""
    if IN_BROWSER or os.getenv("REGQA_SAMPLE_ONLY"):
        return "unavailable"
    try:
        n = _conn(live_roles()[0]).cursor().execute(f"SELECT COUNT(*) FROM {DB}.REG_CLAUSES").fetchone()[0]
    except Exception:
        return "unavailable"
    return "ready" if n else "unavailable"


def is_live() -> bool:
    """Live for the current role only if this deployment can act as it; otherwise that role is replayed."""
    return st.session_state.get("mode", "sample") == "live" and role() in live_roles()


def role() -> str:
    return st.session_state.get("role", "REGQA_COMPLIANCE_LEAD")


def trace() -> mcp.Trace:
    return st.session_state.setdefault("trace", mcp.Trace())


def client(r: str | None = None):
    r = r or role()
    if is_live():
        c = mcp.LiveClient(_conn(r), r, trace())
    else:
        c = mcp.ReplayClient(captured(), r, trace())
    started = st.session_state.setdefault("initialized", set())
    if (r, is_live()) not in started:
        c.initialize()
        c.list_tools()
        started.add((r, is_live()))
    return c


def tools(r: str | None = None) -> list[dict]:
    """tools/list for a role (recorded in the trace)."""
    return client(r).list_tools()


def run_sql_for(r: str):
    """Runs Cortex Analyst's SQL as the given role, so row access policies apply to the results."""
    def run(sql: str):
        if is_live():
            cur = _conn(r).cursor()
            cur.execute(sql)
            return [d[0] for d in cur.description], [list(x) for x in cur.fetchall()]
        out = captured()["sql"].get(r, {}).get(sql)
        if out is None:
            raise RuntimeError("Not captured for this role.")
        if "error" in out:
            raise RuntimeError(out["error"])
        return out["columns"], out["rows"]
    return run


def log_audit(entries: list[dict]) -> None:
    """Live mode: the app appends each MCP call it made to MCP_AUDIT, as the calling role."""
    if not is_live() or not entries:
        return
    cur = _conn(role()).cursor()
    for e in entries:
        try:
            cur.execute(
                f"INSERT INTO {DB}.MCP_AUDIT (EVENT_TS, SESSION_ID, ROLE_NAME, METHOD, TOOL, ARGUMENTS, STATUS, LATENCY_MS, RESULT_BYTES, RESULT_PREVIEW) "
                "SELECT %s, %s, %s, %s, %s, PARSE_JSON(%s), %s, %s, %s, %s",
                (dt.datetime.now().replace(microsecond=0), st.session_state.get("sid", "app"), e["role"], e["method"], e["tool"],
                 json.dumps(e["request"].get("params", {}).get("arguments", {}), ensure_ascii=False),
                 "OK" if e["ok"] else "REFUSED", e["ms"], e["bytes"], json.dumps(e["response"], ensure_ascii=False)[:500]))
        except Exception:  # the auditor role can write; a failed log write never blocks the answer
            pass


@st.cache_data(ttl=20, show_spinner=False)
def live_table(sql: str, r: str) -> pd.DataFrame:
    cur = _conn(r).cursor()
    cur.execute(sql)
    return pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])


def tickets() -> pd.DataFrame:
    if is_live():
        try:
            return live_table(f"SELECT * FROM {DB}.REMEDIATION_TICKETS ORDER BY OPENED_AT DESC", role())
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame(st.session_state.get("tickets", []))


def control_tests() -> pd.DataFrame:
    """Control tests this role may see. Live: the row access policy decides. Sample: same rule, applied here."""
    if is_live():
        try:
            return live_table(f"SELECT * FROM {DB}.CONTROL_TESTS", role())
        except Exception:
            return pd.DataFrame()
    t = _tables()["CONTROL_TESTS"]
    return t[t.BUSINESS_UNIT.isin(ROLES[role()]["business_units"])].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _tables() -> dict[str, pd.DataFrame]:
    return data.generate()


def tables() -> dict[str, pd.DataFrame]:
    return _tables()
