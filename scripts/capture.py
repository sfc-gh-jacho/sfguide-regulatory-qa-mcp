"""Capture real MCP traffic from REGQA_MCP for the browser (sample mode) replay.

    SNOWFLAKE_DEFAULT_CONNECTION_NAME=<connection> python scripts/capture.py

Runs every scripted question as each of the three roles, plus the ticket tool,
and writes data/captured_mcp.json. Requires sql/regqa_setup.sql to have run and
your user to hold the three REGQA_ roles. Tickets it opens are deleted at the end.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from decimal import Decimal
from pathlib import Path

import snowflake.connector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regqa import desk, mcp  # noqa: E402
from regqa.roles import ROLES  # noqa: E402

CONN = os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME", "default")


def plain(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


class Recorder(mcp.LiveClient):
    def __init__(self, conn, role, store):
        super().__init__(conn, role)
        self.store = store

    def call(self, tool, args):
        r = super().call(tool, args)
        e = self.trace[-1]
        self.store["calls"].setdefault(self.role, {})[mcp.key(tool, args)] = {
            "response": e["response"], "http": e["http"], "content_type": e["content_type"], "ms": e["ms"]}
        return r


def main() -> None:
    store = {"captured_at": dt.date.today().isoformat(), "calls": {}, "tools_list": {}, "sql": {},
             "url_template": "https://<account>/api/v2/databases/REGQA_DEMO_DB/schemas/DESK/mcp-servers/REGQA_MCP"}
    for role in ROLES:
        conn = snowflake.connector.connect(connection_name=CONN, role=role, warehouse="REGQA_WH")
        conn.cursor().execute("USE SECONDARY ROLES NONE")
        rec = Recorder(conn, role, store)
        if "initialize" not in store:
            rec.initialize()
            store["initialize"] = {"response": rec.trace[-1]["response"], "http": 200, "content_type": "application/json", "ms": rec.trace[-1]["ms"]}
        rec.list_tools()
        store["tools_list"][role] = {"response": rec.trace[-1]["response"], "http": 200, "content_type": "application/json", "ms": rec.trace[-1]["ms"]}

        def run_sql(sql, conn=conn, role=role):
            cur = conn.cursor()
            try:
                cur.execute(sql)
                out = {"columns": [d[0] for d in cur.description], "rows": [[plain(v) for v in r] for r in cur.fetchall()]}
            except Exception as e:  # recorded so the replay shows the same refusal
                out = {"error": str(e).split("\n")[0][:240]}
            store["sql"].setdefault(role, {})[sql] = out
            if "error" in out:
                raise RuntimeError(out["error"])
            return out["columns"], out["rows"]

        for qid, q in desk.QUESTIONS:
            res = desk.ask(rec, q, run_sql)
            f = desk.finding(res)
            print(f"{role:22s} {qid:10s} {(f or {}).get('verdict') or ('sql' if res['analyst'] else '-'):6s} errors={len(res['errors'])}")
            if f and f.get("verdict") == "GAP":
                t = rec.call("open_remediation_ticket", desk.proposed_ticket(f))
                print(f"{'':22s} {'ticket':10s} {mcp.text_of(t)[:90]}")
        conn.cursor().execute("SELECT 1")
    admin = snowflake.connector.connect(connection_name=CONN)
    admin.cursor().execute("DELETE FROM REGQA_DEMO_DB.DESK.REMEDIATION_TICKETS")
    text = json.dumps(store, indent=1, ensure_ascii=False, default=plain)
    # Request ids in error messages could be traced to the recording account; drop them.
    text = re.sub(r"request-id: [0-9a-f-]{36}", "request-id: <redacted>", text)
    (ROOT / "data" / "captured_mcp.json").write_text(text)
    print("wrote data/captured_mcp.json")


if __name__ == "__main__":
    main()
