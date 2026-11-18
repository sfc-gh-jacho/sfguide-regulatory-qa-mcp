import altair as alt
import pandas as pd
import streamlit as st

from regqa import data, source, ui
from regqa.roles import LABEL, ROLES

st.caption("Control test results this role is allowed to see. Ask questions about them on page 1; Cortex Analyst "
           "writes the SQL and the row access policy filters the rows.")

ct = source.control_tests().copy()
if ct.empty:
    st.warning(f"{LABEL[source.role()]} cannot read control tests.", icon=":material/block:")
    st.stop()
units = sorted(ct.BUSINESS_UNIT.unique())
hidden = [u for u in data.BUSINESS_UNITS if u not in units]
st.markdown(f"Visible business units: **{', '.join(units)}**" + (f" · hidden by policy: {', '.join(hidden)}" if hidden else ""))

ct["FAILED"] = (ct.RESULT == "FAIL").astype(int)
c1, c2, c3 = st.columns(3)
c1.metric("Tests visible", len(ct), border=True)
c2.metric("Failed", int(ct.FAILED.sum()), border=True)
c3.metric("Failure rate", f"{ct.FAILED.mean():.1%}", border=True)

by = ct.groupby(["QUARTER", "BUSINESS_UNIT"], as_index=False).FAILED.mean().rename(columns={"FAILED": "Failure rate"})
st.altair_chart(
    alt.Chart(by).mark_line(point=True).encode(
        x=alt.X("QUARTER:N", title="Quarter"), y=alt.Y("Failure rate:Q", axis=alt.Axis(format="%")),
        color=alt.Color("BUSINESS_UNIT:N", title="Business unit"),
        tooltip=["QUARTER", "BUSINESS_UNIT", alt.Tooltip("Failure rate:Q", format=".1%")]).properties(height=280),
)
top = (ct.groupby(["CONTROL_ID", "CONTROL_NAME", "POLICY_ID"], as_index=False).FAILED.sum()
       .sort_values("FAILED", ascending=False).head(8).rename(columns={"FAILED": "Failures"}))
top["Planted gap"] = top.CONTROL_NAME.isin([g[7] for g in data.GAPS.values()])
st.dataframe(top, hide_index=True, column_config={"Planted gap": st.column_config.CheckboxColumn()})
st.caption("Controls tied to the planted policy gaps fail far more often, as you would expect.")

ui.snowflake_callout("Row access policy on CONTROL_TESTS",
                     f"{LABEL['REGQA_ANALYST']} sees {', '.join(ROLES['REGQA_ANALYST']['business_units'])}; "
                     f"{LABEL['REGQA_COMPLIANCE_LEAD']} sees all three. The same rule applies to SQL, to Cortex Analyst's "
                     "generated SQL and to any MCP client, because it lives on the table.")
