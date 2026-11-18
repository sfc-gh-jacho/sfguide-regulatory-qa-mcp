"""Deploy the app so it is owned by (and runs as) a least-privileged role.

    SNOWFLAKE_DEFAULT_CONNECTION_NAME=<connection> python scripts/deploy_as_role.py [ROLE]

Equivalent to `snow streamlit deploy regqa_desk --role REGQA_COMPLIANCE_LEAD`. Use this
when your connection cannot switch roles (for example an OAuth token issued for one role).
It uploads the artifacts listed in snowflake.yml and creates the app from that stage.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import snowflake.connector
import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLE = sys.argv[1] if len(sys.argv) > 1 else "REGQA_COMPLIANCE_LEAD"
spec = yaml.safe_load((ROOT / "snowflake.yml").read_text())["entities"]["regqa_desk"]

c = snowflake.connector.connect(connection_name=os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME"), role=ROLE,
                                warehouse=spec["query_warehouse"], database="REGQA_DEMO_DB", schema="DESK")
cur = c.cursor()
cur.execute("USE SECONDARY ROLES NONE")
cur.execute("CREATE STAGE IF NOT EXISTS REGQA_APP_STAGE DIRECTORY = (ENABLE = TRUE)")
cur.execute("REMOVE @REGQA_APP_STAGE")
for f in spec["artifacts"]:
    sub = os.path.dirname(f)
    cur.execute(f"PUT 'file://{(ROOT / f).resolve()}' '@REGQA_APP_STAGE{'/' + sub if sub else ''}' AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
eais = ", ".join(spec["external_access_integrations"])
cur.execute(f"""CREATE OR REPLACE STREAMLIT {spec['identifier']['name']}
  FROM '@REGQA_DEMO_DB.DESK.REGQA_APP_STAGE'
  MAIN_FILE = '{spec['main_file']}'
  QUERY_WAREHOUSE = {spec['query_warehouse']}
  RUNTIME_NAME = '{spec['runtime_name']}'
  COMPUTE_POOL = {spec['compute_pool']}
  EXTERNAL_ACCESS_INTEGRATIONS = ({eais})
  TITLE = 'Regulatory Q&A desk'""")
print(cur.fetchone()[0], "as", ROLE)
