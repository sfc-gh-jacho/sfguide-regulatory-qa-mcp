"""The desk's playbook: which MCP tools to call for a question, and how to build the answer.

The playbook is plain code, not a hidden planner, so every step shows up in the
MCP inspector. The AI judgement happens inside the tools: Cortex Search ranks
the text, ASSESS_GAP (AI_COMPLETE) compares a clause with a policy section, and
Cortex Analyst writes SQL. The answer is assembled only from tool results, and
every claim carries the id of the clause or section it came from.
"""

from __future__ import annotations

import json
import re

REG_COLUMNS = ["CLAUSE_ID", "REGULATION_TITLE", "HEADING", "TEXT"]
POL_COLUMNS = ["SECTION_ID", "POLICY_TITLE", "HEADING", "TEXT", "OWNER"]
NUMERIC = re.compile(r"\b(rate|how many|count|trend|failed|failures?|fail|quarter|business unit|by bu|top \d+|most often|exceptions)\b", re.I)
BOILERPLATE = ("Purpose", "Application", "Definitions", "Proportionality", "Governance", "Documentation", "Breaches",
               "Transition", "Scope", "Roles and responsibilities", "Exceptions", "Monitoring", "Review", "Standards")

# Scripted questions: replayed in sample mode, and a good starting set when live.
QUESTIONS = [
    ("incident", "How quickly must we notify the regulator of a major incident, and does our policy meet it?"),
    ("retention", "How long must we keep customer transaction records, and does our records policy comply?"),
    ("mfa", "Do we require multi-factor authentication for remote access, as the cybersecurity rule requires?"),
    ("privileged", "How often must privileged access be recertified, and what does our access standard say?"),
    ("complaints", "How quickly must we acknowledge a customer complaint, and does our procedure meet that?"),
    ("vendors", "Are critical vendors reviewed as often as the third-party risk rule requires?"),
    ("failrate", "What is the control test failure rate by business unit in 2026-Q3?"),
    ("topfails", "Which 5 controls failed most often across all quarters, and how many failures did each have?"),
]


def rows_of(result: dict) -> list[dict]:
    """Search tool results arrive as a JSON array inside a text block."""
    if result.get("isError"):
        return []
    txt = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
    try:
        v = json.loads(txt)
    except ValueError:
        return []
    return v if isinstance(v, list) else v.get("results", []) if isinstance(v, dict) else []


def error_of(result: dict) -> str | None:
    if not result.get("isError"):
        return None
    txt = "".join(c.get("text", "") for c in result.get("content", []))
    if "Could not reach the MCP server" in txt:
        return "could not reach the MCP server (network)"
    if re.search(r"Unknown user-defined function|does not exist or access is not authorized|not authorized|Insufficient privileges", txt):
        obj = re.search(r"(REGQA_DEMO_DB\.DESK\.[A-Z_]+)", txt)
        return (f"refused: this role has no grant on {obj.group(1) if obj else 'the tool'}, so Snowflake treats it "
                "as not found or not authorized")
    return txt.split("\n")[0][:240]


def analyst_parts(result: dict) -> tuple[str, str | None]:
    """Cortex Analyst returns its interpretation and the SQL it wrote; it does not run the SQL."""
    txt = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
    try:
        parts = json.loads(txt)
    except ValueError:
        return txt, None
    words = " ".join(p.get("text", "") for p in parts if "text" in p).strip()
    sql = next((p["statement"] for p in parts if p.get("statement")), None)
    return words, sql


def _substantive(rows: list[dict]) -> list[dict]:
    keep = [r for r in rows if r.get("HEADING") not in BOILERPLATE and not str(r.get("HEADING", "")).endswith(": evidence")]
    return keep or rows


def ask(client, question: str, run_sql=None) -> dict:
    """Run the playbook for one question. `run_sql(sql)` runs Analyst SQL as the client's role."""
    out = {"question": question, "steps": [], "clauses": [], "sections": [], "assessments": [], "analyst": None, "errors": []}

    def step(label, tool, args):
        r = client.call(tool, args)
        err = error_of(r)
        out["steps"].append({"label": label, "tool": tool, "ok": err is None, "error": err})
        if err:
            out["errors"].append(f"{tool}: {err}")
        return r

    if NUMERIC.search(question):
        r = step("Ask Cortex Analyst for SQL", "control_testing_analyst", {"message": question})
        if not r.get("isError"):
            words, sql = analyst_parts(r)
            a = {"interpretation": words, "sql": sql, "rows": None, "columns": None, "sql_error": None}
            if sql and run_sql:
                try:
                    a["columns"], a["rows"] = run_sql(sql)
                except Exception as e:  # shown to the user: the role may not be allowed to run it
                    a["sql_error"] = str(e).split("\n")[0][:240]
            out["analyst"] = a
        return out

    regs = _substantive(rows_of(step("Search the regulations", "regulation_search",
                                     {"query": question, "columns": REG_COLUMNS, "limit": 4})))[:2]
    pols = _substantive(rows_of(step("Search our policies", "policy_search",
                                     {"query": question, "columns": POL_COLUMNS, "limit": 4})))[:2]
    out["clauses"], out["sections"] = regs, pols
    if regs and pols:
        # Compare the best clause with each of the two best sections; keep the first related pair.
        for sec in pols:
            r = step("Assess the gap", "assess_gap", {"clause_ref": regs[0]["CLAUSE_ID"], "section_ref": sec["SECTION_ID"]})
            if r.get("isError"):
                break
            try:
                v = json.loads("".join(c.get("text", "") for c in r.get("content", [])))
            except ValueError:
                continue
            v = json.loads(v) if isinstance(v, str) else v
            v = v[0] if isinstance(v, list) and v else v
            if isinstance(v, dict) and "ASSESS_GAP" in v:
                v = v["ASSESS_GAP"]
            v = json.loads(v) if isinstance(v, str) else v
            v.update({"clause": regs[0], "section": sec})
            out["assessments"].append(v)
            if v.get("verdict") != "NOT_RELATED":
                break
    return out


def finding(res: dict) -> dict | None:
    """The related assessment, if any."""
    return next((a for a in res.get("assessments", []) if a.get("verdict") in ("GAP", "MEETS")), None)


def answer_md(res: dict) -> str:
    """Plain-language answer built only from tool results, with citations."""
    if res.get("analyst"):
        a = res["analyst"]
        if a.get("sql_error"):
            return f"Cortex Analyst wrote the SQL, but this role could not run it: {a['sql_error']}"
        return a.get("interpretation") or "Cortex Analyst answered with the SQL and results below."
    f = finding(res)
    if not f:
        if res.get("errors"):
            return "This role could not get an answer. Every tool call it was not granted was refused by Snowflake."
        return "The search tools did not find a regulation clause and policy section that cover the same obligation."
    c, s = f["clause"], f["section"]
    head = ("**Gap found.** Our policy falls short of the regulation." if f["verdict"] == "GAP"
            else "**Meets the requirement.** Our policy is the same as or stricter than the regulation.")
    return (f"{head}\n\n"
            f"- **Regulation requires** ({c['CLAUSE_ID']}, {c['REGULATION_TITLE']}): {f.get('regulation_requires', c['TEXT'])}\n"
            f"- **Our policy says** ({s['SECTION_ID']}, {s['POLICY_TITLE']}): {f.get('policy_says', s['TEXT'])}\n"
            f"- **Why:** {f.get('explanation', '')}")


def proposed_ticket(f: dict) -> dict:
    c, s = f["clause"], f["section"]
    return {"section_id": s["SECTION_ID"], "clause_id": c["CLAUSE_ID"], "severity": "HIGH",
            "summary": (f"{s['POLICY_TITLE']} {s['SECTION_ID']} falls short of {c['CLAUSE_ID']}, which requires "
                        f"{f.get('regulation_requires', '').rstrip('.')}. Update the policy and its control to match.")[:480]}
