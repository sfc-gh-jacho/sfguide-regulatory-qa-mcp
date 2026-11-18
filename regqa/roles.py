"""The three demo roles and what each is allowed to do. Mirrors sql/regqa_setup.sql."""

ROLES = {
    "REGQA_ANALYST": {
        "label": "Compliance analyst",
        "tools": ["regulation_search", "policy_search", "control_testing_analyst", "assess_gap"],
        "business_units": ["Retail Banking", "Payments"],
        "blurb": "Asks questions and finds gaps. Cannot open tickets. Sees control tests for Retail Banking and Payments only.",
    },
    "REGQA_COMPLIANCE_LEAD": {
        "label": "Compliance lead",
        "tools": ["regulation_search", "policy_search", "control_testing_analyst", "assess_gap", "open_remediation_ticket"],
        "business_units": ["Retail Banking", "Wealth Management", "Payments"],
        "blurb": "Everything the analyst can do, plus approving and opening remediation tickets, across all business units.",
    },
    "REGQA_AUDITOR": {
        "label": "Internal auditor",
        "tools": [],
        "business_units": [],
        "blurb": "Can connect to the MCP server but is granted no tools. Reviews the audit log of every call instead.",
    },
}

LABEL = {k: v["label"] for k, v in ROLES.items()}
ROLE_OF = {v["label"]: k for k, v in ROLES.items()}
