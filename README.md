# Regulatory Q&A Desk on a Snowflake-Managed MCP Server

**Owner:** Janet Cho · **Last reviewed:** November 2026 · **License:** [Apache 2.0](LICENSE)

A compliance desk that checks a bank's policies against regulations through a **Snowflake-managed MCP server**. The Streamlit app is an MCP client: it calls governed Snowflake tools over JSON-RPC and builds every answer only from what those tools return.

| MCP tool | Snowflake object | What it does |
|---|---|---|
| `regulation_search` | Cortex Search service `REG_SEARCH` | Ranks about 160 regulation clauses |
| `policy_search` | Cortex Search service `POLICY_SEARCH` | Ranks about 180 internal policy sections |
| `control_testing_analyst` | Cortex Analyst on semantic view `CONTROL_TESTS_SV` | Writes SQL for questions about 600 control tests |
| `assess_gap` | SQL UDF `ASSESS_GAP` calling `AI_COMPLETE` | Returns MEETS, GAP or NOT_RELATED with reasoning |
| `open_remediation_ticket` | SQL stored procedure | Writes a remediation ticket (compliance lead only) |

The app pages:

1. **Ask the desk:** cited answers, with the regulation clause and policy section side by side, or Cortex Analyst SQL and rows
2. **MCP inspector:** every `initialize`, `tools/list` and `tools/call` request and response, with status, latency and size
3. **Gaps and approvals:** a gap register, and an approval gate before any ticket is written
4. **Control testing:** failure rates by quarter and business unit, filtered by a row access policy

There are also **Audit: what left Snowflake**, **Roles and tool grants** and **About** pages.

- **Landing page and guided walkthrough:** https://sfc-gh-jacho.github.io/sfguide-regulatory-qa-mcp/
- **Try it in your browser (no account):** https://sfc-gh-jacho.github.io/sfguide-regulatory-qa-mcp/try/

## Two modes, one codebase

| | Captured replay | Live Snowflake |
|---|---|---|
| Where | Your browser (stlite), or `streamlit run` on a laptop | Locally against your account, or Streamlit in Snowflake |
| MCP responses | `data/captured_mcp.json`, recorded from the real server by `scripts/capture.py` | JSON-RPC over HTTPS to `REGQA_MCP` in your account |
| Questions | The 8 scripted questions, for each role | Anything |
| AI output | Fixed, from the recorded run | Fresh on each call |
| Roles | Recorded responses per role, including real refusals | Enforced by Snowflake. Locally, one session per role; in Streamlit in Snowflake, the app owner's role (the other roles are replayed) |
| Tickets and audit | Kept in the browser session | Written to `REMEDIATION_TICKETS` and `MCP_AUDIT` |

Every answer in the app is labeled **Replay of a captured MCP call** or **Live call to the MCP server**.

## The three roles

| Role | Tools it can call | Control tests it can see |
|---|---|---|
| `REGQA_COMPLIANCE_LEAD` | All five | All business units |
| `REGQA_ANALYST` | All except `open_remediation_ticket` | Retail Banking and Payments |
| `REGQA_AUDITOR` | None (usage on the server only) | None; reads `MCP_AUDIT` |

`tools/list` returns every tool to any role with usage on the server. Each call is then checked against the role's grant on the underlying search service, semantic view, function or procedure. (Snowflake hides agent tools from roles without usage on the agent; other tool types are listed.)

## Try it locally (no account)

```bash
git clone https://github.com/sfc-gh-jacho/sfguide-regulatory-qa-mcp.git
cd sfguide-regulatory-qa-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install "streamlit==1.65.0" altair
REGQA_SAMPLE_ONLY=1 streamlit run streamlit_app.py
```

`REGQA_SAMPLE_ONLY=1` stops the app from trying to connect to Snowflake. The landing page has a 10-step walkthrough of what to click.

## Run it live in your Snowflake account

### Prerequisites

- **Enterprise Edition or higher**, for row access policies
- **Cortex Search, Cortex Analyst and `AI_COMPLETE`** in your region. The script grants model access (model RBAC) for `llama3.3-70b`, which `ASSESS_GAP` uses, and `claude-sonnet-4-5`, which Cortex Analyst needed in testing. If Cortex Analyst says its models aren't authorized, the error lists the available models; grant the matching `CORTEX-MODEL-ROLE-…` application role, or enable cross-region inference.
- **For Streamlit in Snowflake:** a compute pool for the container runtime and an external access integration for PyPI
- **Snowflake CLI 3.14 or later**, or a Snowsight worksheet
- **Tested with:** Snowflake CLI 3.31, Streamlit 1.65.0, stlite 1.12.2, and the `SYSTEM$ST_CONTAINER_RUNTIME_PY3_11` runtime on an AWS Enterprise Edition account

### Option A: run the app on your laptop

1. **Run the setup script.** Replace `<YOUR_USER>` in [`sql/regqa_setup.sql`](sql/regqa_setup.sql) and run it in a Snowsight worksheet, or with:
   ```bash
   snow sql -c <connection> -f sql/regqa_setup.sql --enable-templating NONE
   ```
   `--enable-templating NONE` is needed because the script contains `&` characters. You can skip the optional `app` step.
2. **Install and run:**
   ```bash
   pip install "streamlit[snowflake]==1.65.0" altair requests
   SNOWFLAKE_DEFAULT_CONNECTION_NAME=<connection> streamlit run streamlit_app.py
   ```
3. **Choose Live Snowflake** in the sidebar. The app opens one connector session per role, with `USE SECONDARY ROLES NONE`, so each call runs with only that role's grants.

### Option B: deploy to Streamlit in Snowflake

1. **Run the `app` step** of the setup script after setting `<YOUR_ORG>-<YOUR_ACCOUNT>` (with hyphens) and your compute pool and PyPI integration names. It lets `REGQA_COMPLIANCE_LEAD` own the app and creates `REGQA_MCP_ACCESS`, an external access integration that allows only your account host on port 443, so the app can reach its own MCP endpoint.
2. **Set your names** in `snowflake.yml` (`compute_pool`, `external_access_integrations`).
3. **Deploy as the lead,** so the app runs with the lead's grants and nothing more:
   ```bash
   snow streamlit deploy regqa_desk -c <connection> --role REGQA_COMPLIANCE_LEAD
   ```
   If your connection can't switch roles (for example, an OAuth token issued for one role), run `SNOWFLAKE_DEFAULT_CONNECTION_NAME=<connection> python scripts/deploy_as_role.py`. Snowflake doesn't support transferring ownership of a Streamlit app, so deploy as the role you want it to run as.

### Clean up

Uncomment and run the `cleanup` step. Dropping `REGQA_DEMO_DB` also removes the app, the MCP server and the search services.

### Connect Claude, Cursor or another MCP client

Create an OAuth security integration as described in [Snowflake-managed MCP server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp), set the user's default role to one of the `REGQA_` roles, and use this server URL (hyphens, not underscores, in the host):

```
https://<org>-<account>.snowflakecomputing.com/api/v2/databases/REGQA_DEMO_DB/schemas/DESK/mcp-servers/REGQA_MCP
```

## Change the data or re-record the replay

- **Data:** edit `regqa/data.py`, then run `python scripts/make_sql.py` to regenerate `sql/regqa_setup.sql` from `sql/regqa_setup.template.sql`.
- **Replay:** after setup, run `SNOWFLAKE_DEFAULT_CONNECTION_NAME=<connection> python scripts/capture.py`. It asks every scripted question as each role, opens and then deletes test tickets, and writes `data/captured_mcp.json`. Your user needs all three `REGQA_` roles.

## What gets created

| Object | Name |
|---|---|
| Database and schema | `REGQA_DEMO_DB.DESK` |
| Warehouse | `REGQA_WH` (XSMALL, 60-second auto-suspend) |
| Tables | `REGULATIONS` (12), `REG_CLAUSES` (160), `POLICIES` (20), `POLICY_SECTIONS` (180), `CONTROLS` (50), `CONTROL_TESTS` (600), `BU_ACCESS`, `REMEDIATION_TICKETS`, `MCP_AUDIT` |
| Cortex Search services | `REG_SEARCH`, `POLICY_SEARCH` |
| Semantic view | `CONTROL_TESTS_SV` |
| Function and procedure | `ASSESS_GAP`, `OPEN_REMEDIATION_TICKET` |
| MCP server | `REGQA_MCP` |
| Row access policy | `regqa_bu_policy` on `CONTROL_TESTS` |
| Roles | `REGQA_ANALYST`, `REGQA_COMPLIANCE_LEAD`, `REGQA_AUDITOR` |
| Optional | Network rule `REGQA_MCP_EGRESS`, integration `REGQA_MCP_ACCESS`, Streamlit app `REGULATORY_QA_DESK` |

## Cost and time

- **Time:** about 10 minutes to click through in your browser, and about 20 minutes to set up live mode.
- **Compute:** the setup script runs in about a minute on an XSMALL warehouse, plus the initial build of the two search services. In testing, search calls returned in about half a second, and each gap assessment or Cortex Analyst call took 5 to 12 seconds. Recording the replay made about 60 tool calls. The Streamlit container uses its compute pool while the app is open.
- **Validation:** tested November 18, 2026 on an Enterprise Edition account (AWS):
  - The setup script ran clean on a fresh database and again on a rerun.
  - `ASSESS_GAP` returned the expected verdict for all 34 test pairs: 5 planted gaps, 27 met requirements and 2 unrelated pairs.
  - All 8 scripted questions returned the expected answer for each role, over the real MCP server.
  - The analyst's ticket call and all of the auditor's calls were refused by Snowflake. The row access policy returned 2 business units to the analyst and 3 to the lead.
  - All pages were clicked through with no exceptions in replay mode, live mode, and the browser build (which loaded in about 13 seconds).
  - The app was deployed to Streamlit in Snowflake, owned by `REGQA_COMPLIANCE_LEAD`, and `SHOW STREAMLITS` confirmed it. A live MCP call from inside Streamlit in Snowflake was not verified.

## Known limitations

- **The playbook is simple on purpose.** The app follows a fixed, visible sequence (search, search, assess, or ask Cortex Analyst), so every step shows in the inspector. For governed business questions, Snowflake recommends exposing a Cortex Agent as the single client-facing tool and letting it orchestrate the others.
- **Gap verdicts are AI judgements.** The gap tool matched every test pair here, but a person should confirm each gap before acting on it.
- **The replay only covers the scripted questions.** Free-text questions need live mode.
- **Streamlit in Snowflake runs as one role.** The app owner's role is live, and the other two are shown from the replay.
- **Audit records come from the app.** `MCP_AUDIT` is written by this app. Other MCP clients' calls appear in Snowflake's query history, not in this table.
- **The browser version uses a CDN.** stlite and Pyodide load from jsDelivr; the landing page loads no third-party resources.

## Customize with Cortex Code

[Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) can adapt this desk to your environment. Open the repo folder in Cortex Code and try prompts like:

- "Explain this MCP server's five tools and the grants behind each one, then map them to my policy library and regulatory obligations register without changing any objects."
- "Replace the playbook with a Cortex Agent that orchestrates regulation_search, policy_search, assess_gap and control_testing_analyst, expose the agent as the only tool on a new MCP server, and propose least-privilege grants first."
- "Load our real policy PDFs from a stage with AI_PARSE_DOCUMENT, chunk them into POLICY_SECTIONS, and rebuild the policy search service. Show me a sample of the chunks before you rebuild."

Ask it to review the plan with you before it creates or changes any objects in your account.

## Repository layout

```
LICENSE                        Apache License 2.0
index.html, styles.css,        GitHub Pages landing page and walkthrough (no third-party requests)
  script.js
try/index.html                 In-browser version (stlite)
docs/images/                   Screenshots of the running app
streamlit_app.py               App entry point, navigation and role switch
app_pages/                     One file per screen
regqa/data.py                  Deterministic synthetic regulations, policies and control tests
regqa/mcp.py                   MCP client (JSON-RPC over HTTPS, SSE) and the replay client
regqa/desk.py                  The visible playbook and answer assembly
regqa/source.py                Replay vs live, sessions per role, tickets and audit
regqa/roles.py, regqa/ui.py    Role definitions and shared UI
data/captured_mcp.json         MCP traffic recorded from the real server
sql/regqa_setup.template.sql   Setup script template (edit this, not the generated file)
sql/regqa_setup.sql            Generated setup script with data, checks and cleanup
scripts/make_sql.py            Builds the setup script from the generator
scripts/capture.py             Records the replay from a live server
scripts/deploy_as_role.py      Deploys the app as a least-privileged role
snowflake.yml                  Streamlit in Snowflake manifest
pyproject.toml                 Pinned dependencies for live mode
.streamlit/config.toml         Snowflake theme
static/                        Inter and JetBrains Mono fonts (SIL Open Font License)
```

## License

Licensed under the [Apache License, Version 2.0](LICENSE). The bundled Inter and JetBrains Mono fonts are under the SIL Open Font License.

## Disclaimer

This is an illustrative example provided as-is. It is not an official Snowflake product, it is not supported by Snowflake Support, and it is not legal or regulatory advice.

Everything in it is synthetic. The Northbridge Financial Conduct Authority, Harborline Bank, their rules, policies, owners and control test results are fictional, and counts describe this data set only. The repository contains no credentials, account identifiers or connection details. Review and test before any production use, and remember that MCP tool results leave Snowflake: they go to the MCP client and, through it, to any model provider it uses.
