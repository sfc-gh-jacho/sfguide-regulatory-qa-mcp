"""Write sql/regqa_setup.sql from the template and the synthetic data generator.

    python scripts/make_sql.py

Edit regqa/data.py to change the data, then run this again.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regqa import data  # noqa: E402

ORDER = ["REGULATIONS", "REG_CLAUSES", "POLICIES", "POLICY_SECTIONS", "CONTROLS", "CONTROL_TESTS"]


def lit(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return "NULL"
    if isinstance(v, (dt.date, dt.datetime)):
        return f"'{v.isoformat()}'"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def inserts(name, df, batch=200) -> str:
    cols = ", ".join(df.columns)
    rows = [f"({', '.join(lit(v) for v in r)})" for r in df.itertuples(index=False)]
    out = []
    for i in range(0, len(rows), batch):
        out.append(f"INSERT INTO {name} ({cols}) VALUES\n  " + ",\n  ".join(rows[i:i + batch]) + ";")
    return "\n".join(out)


def main() -> None:
    t = data.generate()
    body = "\n\n".join(f"-- {n}: {len(t[n])} rows\n" + inserts(n, t[n]) for n in ORDER)
    tpl = (ROOT / "sql" / "regqa_setup.template.sql").read_text()
    (ROOT / "sql" / "regqa_setup.sql").write_text(tpl.replace("{{DATA}}", body))
    print("wrote sql/regqa_setup.sql", {n: len(t[n]) for n in ORDER})


if __name__ == "__main__":
    main()
