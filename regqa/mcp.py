"""A small MCP client for the Snowflake-managed MCP server, plus a replay client.

The live client speaks JSON-RPC 2.0 over HTTPS to
    https://<account>/api/v2/databases/<db>/schemas/<schema>/mcp-servers/<name>
and authenticates with the token of an existing Snowflake connector session, so it
uses whichever role that session is running as. It records every request and
response so the app can show exactly what crossed the wire.

The replay client returns responses captured from that same server (see
scripts/capture.py), so the app can run in a browser with no Snowflake account.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import time
import uuid

DB, SCHEMA, SERVER = "REGQA_DEMO_DB", "DESK", "REGQA_MCP"
PROTOCOL = "2025-06-18"


def key(tool: str, args: dict) -> str:
    return tool + " " + json.dumps(args, sort_keys=True, ensure_ascii=False)


def text_of(result: dict) -> str:
    """The text content of a tools/call result."""
    return "".join(c.get("text", "") for c in (result or {}).get("content", []) if c.get("type") == "text")


class Trace(list):
    """Everything a client sent and received, oldest first."""

    def add(self, role, method, tool, request, response, http, content_type, ms) -> dict:
        body = json.dumps(response, ensure_ascii=False)
        e = {"id": len(self) + 1, "ts": dt.datetime.now().strftime("%H:%M:%S"), "role": role, "method": method,
             "tool": tool, "request": request, "response": response, "http": http, "content_type": content_type,
             "ms": ms, "bytes": len(body.encode("utf-8")),
             "ok": "error" not in response and not response.get("result", {}).get("isError", False)}
        self.append(e)
        return e


class LiveClient:
    """Calls the real MCP server as the role of `conn` (a snowflake.connector connection)."""

    live = True

    def __init__(self, conn, role: str, trace: Trace | None = None):
        import requests

        self._requests = requests
        self.conn, self.role = conn, role
        self.trace = trace if trace is not None else Trace()
        self.session_id = str(uuid.uuid4())[:8]
        # MCP clients have trouble with underscores in hostnames; Snowflake also serves the hyphenated host.
        host = os.getenv("REGQA_MCP_HOST") or conn.host
        self.url = f"https://{host.replace('_', '-')}/api/v2/databases/{DB}/schemas/{SCHEMA}/mcp-servers/{SERVER}"
        self._next = 0

    def _post(self, method: str, params: dict, tool: str | None = None) -> dict:
        self._next += 1
        req = {"jsonrpc": "2.0", "id": self._next, "method": method, "params": params}
        for attempt in (1, 2):
            headers = {"Authorization": f'Snowflake Token="{self.conn.rest.token}"', "Content-Type": "application/json",
                       "Accept": "application/json, text/event-stream"}
            t = time.perf_counter()
            try:
                r = self._requests.post(self.url, headers=headers, json=req, timeout=300)
            except self._requests.RequestException as e:  # network or TLS failure: show it, don't crash
                msg = {"jsonrpc": "2.0", "id": self._next, "error": {"code": -32000, "message": f"Could not reach the MCP server: {e}"[:400]}}
                self.trace.add(self.role, method, tool, req, msg, 0, "network error", round((time.perf_counter() - t) * 1000))
                return msg
            ms = round((time.perf_counter() - t) * 1000)
            if r.status_code == 401 and attempt == 1:
                self.conn.cursor().execute("SELECT 1")  # lets the connector renew its session token
                continue
            break
        r.encoding = "utf-8"  # the event stream does not declare a charset
        ctype = r.headers.get("content-type", "").split(";")[0]
        if ctype == "text/event-stream":
            events = [ln[5:].strip() for ln in r.text.splitlines() if ln.startswith("data:")]
            events = [e for e in events if e and e != "[DONE]"]
            msg = json.loads(events[-1]) if events else {"error": {"message": "empty event stream"}}
        else:
            try:
                msg = r.json()
            except ValueError:
                msg = {"error": {"code": r.status_code, "message": r.text[:500]}}
        self.trace.add(self.role, method, tool, req, msg, r.status_code, ctype, ms)
        return msg

    def initialize(self) -> dict:
        return self._post("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                         "clientInfo": {"name": "regulatory-qa-desk", "version": "1.0"}})

    def list_tools(self) -> list[dict]:
        return self._post("tools/list", {}).get("result", {}).get("tools", [])

    def call(self, tool: str, args: dict) -> dict:
        msg = self._post("tools/call", {"name": tool, "arguments": args}, tool)
        return msg.get("result") or {"isError": True, "content": [{"type": "text", "text": json.dumps(msg.get("error"))}]}


class ReplayClient:
    """Answers from responses captured from the real server, per role. Same interface as LiveClient."""

    live = False

    def __init__(self, captured: dict, role: str, trace: Trace | None = None):
        self.cap, self.role = captured, role
        self.trace = trace if trace is not None else Trace()
        self.url = captured.get("url_template", f"https://<account>/api/v2/databases/{DB}/schemas/{SCHEMA}/mcp-servers/{SERVER}")
        self._next = 0

    def _replay(self, method, params, tool, entry):
        self._next += 1
        req = {"jsonrpc": "2.0", "id": self._next, "method": method, "params": params}
        resp = dict(entry["response"])
        resp["id"] = self._next
        self.trace.add(self.role, method, tool, req, resp, entry.get("http", 200), entry.get("content_type", "text/event-stream"), entry.get("ms", 0))
        return resp

    def initialize(self) -> dict:
        return self._replay("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                           "clientInfo": {"name": "regulatory-qa-desk", "version": "1.0"}}, None, self.cap["initialize"])

    def list_tools(self) -> list[dict]:
        return self._replay("tools/list", {}, None, self.cap["tools_list"][self.role]).get("result", {}).get("tools", [])

    def has(self, tool: str, args: dict) -> bool:
        return key(tool, args) in self.cap["calls"].get(self.role, {})

    def call(self, tool: str, args: dict) -> dict:
        entry = self.cap["calls"].get(self.role, {}).get(key(tool, args))
        if entry is None:
            entry = {"response": {"jsonrpc": "2.0", "result": {"isError": True, "content": [{"type": "text", "text":
                     "Not captured: sample mode can replay only the scripted questions. Connect to Snowflake to ask anything."}]}},
                     "http": 0, "content_type": "replay", "ms": 0}
        return self._replay("tools/call", {"name": tool, "arguments": args}, tool, entry).get("result", {})
