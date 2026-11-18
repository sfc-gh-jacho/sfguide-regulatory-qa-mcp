"""Synthetic regulations, internal policies and control-test results.

Everything here is fictional. The regulator, the bank, the rules and the people
are invented for the demo. Five policy sections are planted to fall short of a
regulation (see GAPS); every other requirement is met, so a good answer has to
tell the two apart.
"""

from __future__ import annotations

import datetime as dt
import random

import pandas as pd

SEED = 2026
REGULATOR = "Northbridge Financial Conduct Authority (NFCA, fictional)"
BANK = "Harborline Bank (fictional)"
AS_OF = dt.date(2026, 11, 10)
QUARTERS = ["2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3"]
QUARTER_END = {"2025-Q4": dt.date(2025, 12, 31), "2026-Q1": dt.date(2026, 3, 31),
               "2026-Q2": dt.date(2026, 6, 30), "2026-Q3": dt.date(2026, 9, 30)}
BUSINESS_UNITS = ["Retail Banking", "Wealth Management", "Payments"]

# id, title, effective date, short scope
REGULATIONS = [
    ("NFCA-R01", "Operational Resilience Rule", "2025-03-31", "important business services and the incidents that disrupt them"),
    ("NFCA-R02", "Cybersecurity Requirements", "2025-06-30", "information security controls over systems and data"),
    ("NFCA-R03", "Records and Retention Rule", "2024-12-31", "the creation, retention and retrieval of business records"),
    ("NFCA-R04", "Third-Party Risk Rule", "2025-09-30", "outsourcing and reliance on third-party service providers"),
    ("NFCA-R05", "Complaints Handling Rule", "2025-01-31", "the receipt, handling and resolution of customer complaints"),
    ("NFCA-R06", "Anti-Money Laundering Program Rule", "2024-06-30", "the firm's anti-money laundering program"),
    ("NFCA-R07", "Sanctions Compliance Rule", "2024-09-30", "screening customers and payments against sanctions lists"),
    ("NFCA-R08", "Model Risk Management Rule", "2025-12-31", "models used in decisions, pricing, risk and reporting"),
    ("NFCA-R09", "Customer Data Privacy Rule", "2025-04-30", "the processing and protection of customer personal data"),
    ("NFCA-R10", "Suitability and Disclosure Rule", "2025-07-31", "advice, product suitability and client disclosures"),
    ("NFCA-R11", "Market Conduct Rule", "2025-02-28", "trading communications and market surveillance"),
    ("NFCA-R12", "Governance and Accountability Rule", "2024-12-31", "board oversight and senior management accountability"),
]

# key, regulation, clause, requirement (regulator wording), policy, section,
# policy wording, control name, compliant
REQUIREMENTS = [
    ("INCIDENT_NOTIFY", "NFCA-R01", "4.2", "A firm must notify the Authority of a major operational incident within 72 hours of determining that the incident is major.",
     "POL-07", "4", "The Incident Manager notifies the regulator of a major operational incident within 7 calendar days of classification.",
     "Regulatory incident notification timeliness", False),
    ("IMPACT_TOLERANCE", "NFCA-R01", "3.1", "A firm must set an impact tolerance for each important business service and review it at least annually.",
     "POL-02", "3", "Each important business service has an approved impact tolerance that the Resilience Office reviews at least annually.",
     "Impact tolerance annual review", True),
    ("BCP_TEST", "NFCA-R01", "5.3", "A firm must test its ability to remain within impact tolerance through scenario testing at least annually.",
     "POL-02", "5", "Scenario tests covering every important business service run at least once a year, with results reported to the Operational Risk Committee.",
     "Annual resilience scenario testing", True),
    ("MFA", "NFCA-R02", "3.4", "A firm must require multi-factor authentication for all remote access to its systems and for all privileged accounts.",
     "POL-05", "3", "Multi-factor authentication is mandatory for all remote access and for every privileged account.",
     "Multi-factor authentication coverage", True),
    ("PRIV_RECERT", "NFCA-R02", "3.6", "A firm must recertify privileged access rights at least quarterly.",
     "POL-05", "4", "System owners recertify privileged access rights semi-annually.",
     "Privileged access recertification", False),
    ("PATCH_CRITICAL", "NFCA-R02", "4.1", "A firm must remediate critical security vulnerabilities on internet-facing systems within 14 days of a patch becoming available.",
     "POL-06", "3", "Critical vulnerabilities on internet-facing systems are patched within 14 days of patch release.",
     "Critical patch remediation within 14 days", True),
    ("ENCRYPTION", "NFCA-R02", "4.5", "A firm must encrypt customer data at rest and in transit using industry-standard cryptography.",
     "POL-06", "5", "Customer data is encrypted at rest and in transit using approved industry-standard algorithms.",
     "Encryption of customer data", True),
    ("RETENTION", "NFCA-R03", "2.1", "A firm must retain records of customer transactions and communications for at least seven years.",
     "POL-11", "3", "Customer transaction and communication records are retained for five years and then deleted.",
     "Record retention period", False),
    ("RETRIEVAL", "NFCA-R03", "2.4", "A firm must be able to produce any retained record to the Authority within three business days of a request.",
     "POL-11", "5", "Records requested by a regulator are produced within three business days.",
     "Regulatory record retrieval", True),
    ("IMMUTABLE", "NFCA-R03", "3.2", "A firm must store retained records in a form that prevents alteration or deletion during the retention period.",
     "POL-11", "4", "Retained records are held in write-once storage that prevents alteration or early deletion.",
     "Immutable record storage", True),
    ("VENDOR_REVIEW", "NFCA-R04", "3.3", "A firm must review the risk of each critical third-party service provider at least annually.",
     "POL-14", "4", "Critical vendors receive a full risk review every 24 months.",
     "Critical vendor periodic risk review", False),
    ("VENDOR_DD", "NFCA-R04", "2.2", "A firm must complete due diligence on a third-party service provider before entering into a contract.",
     "POL-14", "3", "Due diligence is completed and approved before any third-party contract is signed.",
     "Pre-contract vendor due diligence", True),
    ("EXIT_PLAN", "NFCA-R04", "4.1", "A firm must maintain a tested exit plan for each critical third-party service provider.",
     "POL-14", "5", "Each critical vendor has an exit plan that is tested at least every two years.",
     "Critical vendor exit plans", True),
    ("COMPLAINT_ACK", "NFCA-R05", "2.1", "A firm must acknowledge a customer complaint in writing within five business days of receipt.",
     "POL-16", "3", "Complaints are acknowledged in writing within 10 business days of receipt.",
     "Complaint acknowledgement timeliness", False),
    ("COMPLAINT_FINAL", "NFCA-R05", "2.3", "A firm must send a final response to a complaint within eight weeks of receipt.",
     "POL-16", "4", "A final response is issued within eight weeks of receiving a complaint.",
     "Complaint final response within eight weeks", True),
    ("COMPLAINT_RCA", "NFCA-R05", "3.1", "A firm must analyse complaint root causes at least quarterly and report themes to senior management.",
     "POL-16", "5", "Complaint root causes are analysed every quarter and themes are reported to the Executive Committee.",
     "Quarterly complaint root-cause analysis", True),
    ("AML_TRAINING", "NFCA-R06", "3.2", "A firm must provide anti-money laundering training to relevant staff at least annually.",
     "POL-09", "4", "All relevant staff complete anti-money laundering training every year.",
     "Annual AML training completion", True),
    ("SAR_FILING", "NFCA-R06", "4.1", "A firm must file a suspicious activity report within 30 days of determining that activity is suspicious.",
     "POL-09", "5", "Suspicious activity reports are filed within 30 days of the suspicion determination.",
     "Suspicious activity report timeliness", True),
    ("CDD_REFRESH", "NFCA-R06", "2.4", "A firm must refresh customer due diligence for high-risk customers at least annually.",
     "POL-10", "3", "Customer due diligence for high-risk customers is refreshed every 12 months.",
     "High-risk customer due diligence refresh", True),
    ("SANCTIONS_ONBOARD", "NFCA-R07", "2.1", "A firm must screen every new customer against applicable sanctions lists before establishing the relationship.",
     "POL-12", "3", "Every prospective customer is screened against sanctions lists before an account is opened.",
     "Sanctions screening at onboarding", True),
    ("SANCTIONS_LIST", "NFCA-R07", "2.3", "A firm must apply updates to sanctions lists in its screening systems within 24 hours of publication.",
     "POL-12", "4", "Sanctions list updates are loaded into screening systems within 24 hours of publication.",
     "Sanctions list update timeliness", True),
    ("SANCTIONS_PAYMENTS", "NFCA-R07", "3.1", "A firm must screen outgoing payments against sanctions lists before release.",
     "POL-12", "5", "Outgoing payments are screened against sanctions lists before they are released.",
     "Payment sanctions screening", True),
    ("MODEL_VALIDATION", "NFCA-R08", "3.1", "A firm must independently validate each high-materiality model before use and at least annually thereafter.",
     "POL-18", "4", "High-materiality models are independently validated before first use and annually after that.",
     "Annual validation of high-materiality models", True),
    ("MODEL_INVENTORY", "NFCA-R08", "2.1", "A firm must maintain a complete inventory of models with an accountable owner for each.",
     "POL-18", "3", "The Model Risk team maintains a complete model inventory, and every model has a named owner.",
     "Model inventory completeness", True),
    ("PRIVACY_BREACH", "NFCA-R09", "4.2", "A firm must inform affected customers of a personal data breach that is likely to cause them harm without undue delay.",
     "POL-08", "4", "Customers affected by a harmful personal data breach are informed without undue delay.",
     "Customer breach notification", True),
    ("DSAR", "NFCA-R09", "3.3", "A firm must respond to a customer's request for access to their personal data within 30 days.",
     "POL-08", "5", "Data subject access requests are answered within 30 days.",
     "Data access request timeliness", True),
    ("SUITABILITY", "NFCA-R10", "2.2", "A firm must review the suitability of ongoing advice for each advised client at least annually.",
     "POL-19", "3", "Advisers review the suitability of each advised client's portfolio every year.",
     "Annual suitability review", True),
    ("DISCLOSURE", "NFCA-R10", "3.1", "A firm must give a client a written disclosure of all costs and charges before providing advice.",
     "POL-19", "4", "Clients receive a written disclosure of all costs and charges before advice is given.",
     "Pre-advice cost disclosure", True),
    ("COMMS_RETENTION", "NFCA-R11", "2.1", "A firm must record and retain electronic communications relating to trading activity.",
     "POL-20", "3", "All trading-related electronic communications are recorded and retained.",
     "Trading communications capture", True),
    ("SURVEILLANCE", "NFCA-R11", "3.2", "A firm must monitor trading activity to detect potential market abuse and review alerts within five business days.",
     "POL-20", "4", "Market abuse surveillance alerts are reviewed within five business days.",
     "Surveillance alert review timeliness", True),
    ("BOARD_REPORT", "NFCA-R12", "2.3", "A firm's board must receive a compliance report at least quarterly.",
     "POL-01", "4", "The Chief Compliance Officer reports to the board every quarter.",
     "Quarterly board compliance reporting", True),
    ("RESP_MAP", "NFCA-R12", "3.1", "A firm must maintain a responsibilities map that assigns each regulatory obligation to a named senior manager.",
     "POL-01", "5", "A responsibilities map assigns every regulatory obligation to a named senior manager and is kept current.",
     "Senior manager responsibilities map", True),
]

GAPS = {r[0]: r for r in REQUIREMENTS if not r[8]}

POLICIES = [
    ("POL-01", "Compliance Governance Policy", "Chief Compliance Officer", "NFCA-R12"),
    ("POL-02", "Operational Resilience Policy", "Head of Resilience", "NFCA-R01"),
    ("POL-03", "Business Continuity Standard", "Head of Resilience", "NFCA-R01"),
    ("POL-04", "Information Security Policy", "Chief Information Security Officer", "NFCA-R02"),
    ("POL-05", "Identity and Access Management Standard", "Chief Information Security Officer", "NFCA-R02"),
    ("POL-06", "Vulnerability and Encryption Standard", "Chief Information Security Officer", "NFCA-R02"),
    ("POL-07", "Cyber Incident Response Policy", "Head of Security Operations", "NFCA-R01"),
    ("POL-08", "Customer Data Privacy Policy", "Data Protection Officer", "NFCA-R09"),
    ("POL-09", "Anti-Money Laundering Policy", "Money Laundering Reporting Officer", "NFCA-R06"),
    ("POL-10", "Customer Due Diligence Standard", "Money Laundering Reporting Officer", "NFCA-R06"),
    ("POL-11", "Records Management Policy", "Head of Records Management", "NFCA-R03"),
    ("POL-12", "Sanctions Policy", "Head of Financial Crime", "NFCA-R07"),
    ("POL-13", "Outsourcing Policy", "Chief Procurement Officer", "NFCA-R04"),
    ("POL-14", "Third-Party Risk Management Standard", "Chief Procurement Officer", "NFCA-R04"),
    ("POL-15", "Customer Treatment Policy", "Head of Customer Experience", "NFCA-R05"),
    ("POL-16", "Complaints Handling Procedure", "Head of Customer Experience", "NFCA-R05"),
    ("POL-17", "Data Governance Policy", "Chief Data Officer", "NFCA-R09"),
    ("POL-18", "Model Risk Management Policy", "Head of Model Risk", "NFCA-R08"),
    ("POL-19", "Advice and Suitability Policy", "Head of Wealth Compliance", "NFCA-R10"),
    ("POL-20", "Trading Conduct Policy", "Head of Markets Compliance", "NFCA-R11"),
]

GENERIC_CLAUSES = [
    ("1.1", "Purpose", "This rule sets out the Authority's requirements for {scope}."),
    ("1.2", "Application", "This rule applies to every firm authorised by the Authority, including branches that serve customers in its jurisdiction."),
    ("1.3", "Definitions", "In this rule, 'senior manager' means an individual approved by the Authority to hold a senior management function."),
    ("1.4", "Proportionality", "A firm must apply this rule in a way that is proportionate to the nature, scale and complexity of its business."),
    ("5.1", "Governance", "A firm's board is responsible for approving the policies that implement this rule and for overseeing their effectiveness."),
    ("5.2", "Documentation", "A firm must document how it meets each requirement of this rule and keep that documentation up to date."),
    ("6.1", "Breaches", "A firm must notify the Authority promptly if it becomes aware that it has breached this rule."),
    ("6.2", "Transition", "A firm must comply with this rule from its effective date unless the Authority has granted a written waiver."),
]

GENERIC_SECTIONS = [
    ("1", "Purpose", "This policy describes how {bank} meets its obligations for {topic}."),
    ("2", "Scope", "This policy applies to all employees, contractors and business units of {bank}, including Retail Banking, Wealth Management and Payments."),
    ("6", "Roles and responsibilities", "The {owner} owns this policy. Business unit heads are accountable for applying it in their areas."),
    ("7", "Exceptions", "Exceptions to this policy require written approval from the {owner} and are recorded in the exceptions register."),
    ("8", "Monitoring", "Compliance with this policy is tested by the second line of defence, and results are reported to the Risk Committee."),
    ("9", "Review", "The {owner} reviews this policy at least annually and after any material regulatory change."),
]

OWNERS = ["A. Okafor", "B. Lindqvist", "C. Moreau", "D. Haddad", "E. Novak", "F. Tanaka", "G. Reyes", "H. Brennan",
          "I. Kowalski", "J. Mensah", "K. Ivanova", "L. Fischer"]

EXTRA_CONTROLS = [
    ("POL-04", "NFCA-R02", "Security awareness training completion"),
    ("POL-04", "NFCA-R02", "Phishing simulation follow-up"),
    ("POL-03", "NFCA-R01", "Business continuity plan currency"),
    ("POL-13", "NFCA-R04", "Outsourcing register completeness"),
    ("POL-15", "NFCA-R05", "Vulnerable customer flagging"),
    ("POL-17", "NFCA-R09", "Data lineage for regulatory reports"),
    ("POL-10", "NFCA-R06", "Beneficial ownership verification"),
    ("POL-13", "NFCA-R04", "Intragroup outsourcing agreements"),
    ("POL-17", "NFCA-R09", "Personal data inventory currency"),
    ("POL-03", "NFCA-R01", "Crisis communication call tree test"),
    ("POL-18", "NFCA-R08", "Model performance monitoring"),
    ("POL-20", "NFCA-R11", "Personal account dealing pre-clearance"),
    ("POL-09", "NFCA-R06", "Transaction monitoring tuning review"),
    ("POL-15", "NFCA-R05", "Fair value assessment of products"),
    ("POL-01", "NFCA-R12", "Regulatory change log maintenance"),
    ("POL-08", "NFCA-R09", "Privacy notice accuracy"),
    ("POL-06", "NFCA-R02", "Encryption key rotation"),
    ("POL-11", "NFCA-R03", "Legal hold application"),
]


def _regulations() -> tuple[pd.DataFrame, pd.DataFrame]:
    regs, clauses = [], []
    for rid, title, eff, scope in REGULATIONS:
        regs.append({"REGULATION_ID": rid, "TITLE": title, "REGULATOR": REGULATOR, "EFFECTIVE_DATE": dt.date.fromisoformat(eff), "SCOPE": scope})
        own = [r for r in REQUIREMENTS if r[1] == rid]
        rows = [(c, h, t.format(scope=scope)) for c, h, t in GENERIC_CLAUSES]
        rows += [(r[2], r[7], r[3]) for r in own]
        # Supporting clauses so each rule reads like a full document
        for i, r in enumerate(own, 1):
            rows.append((f"{r[2].split('.')[0]}.{int(r[2].split('.')[1]) + 5}", f"{r[7]}: evidence",
                         f"A firm must keep evidence that it meets clause {r[2]} and make that evidence available to the Authority on request."))
        for clause, heading, text in sorted(rows, key=lambda x: tuple(int(p) for p in x[0].split("."))):
            clauses.append({"CLAUSE_ID": f"{rid} §{clause}", "REGULATION_ID": rid, "REGULATION_TITLE": title,
                            "CLAUSE": clause, "HEADING": heading, "TEXT": text, "EFFECTIVE_DATE": dt.date.fromisoformat(eff)})
    return pd.DataFrame(regs), pd.DataFrame(clauses)


def _policies() -> tuple[pd.DataFrame, pd.DataFrame]:
    pols, sections = [], []
    for pid, title, owner, rid in POLICIES:
        topic = next(r[3] for r in REGULATIONS if r[0] == rid)
        pols.append({"POLICY_ID": pid, "TITLE": title, "OWNER": owner, "PRIMARY_REGULATION": rid,
                     "VERSION": "3.2" if pid in ("POL-07", "POL-11") else "4.0", "LAST_REVIEWED": dt.date(2026, 2, 27)})
        rows = [(s, h, t.format(bank=BANK, topic=topic, owner=owner)) for s, h, t in GENERIC_SECTIONS]
        own = [r for r in REQUIREMENTS if r[4] == pid]
        rows += [(r[5], r[7], r[6]) for r in own]
        used = {r[0] for r in rows}
        for s in ("3", "4", "5"):
            if s not in used:
                rows.append((s, "Standards", f"Business units follow the procedures in this policy for {topic}, and record evidence in the control library."))
        for sec, heading, text in sorted(rows, key=lambda x: int(x[0])):
            sections.append({"SECTION_ID": f"{pid} §{sec}", "POLICY_ID": pid, "POLICY_TITLE": title, "SECTION": sec,
                             "HEADING": heading, "TEXT": text, "OWNER": owner})
    return pd.DataFrame(pols), pd.DataFrame(sections)


def _controls() -> pd.DataFrame:
    rows = []
    for i, r in enumerate(REQUIREMENTS, 1):
        rows.append({"CONTROL_ID": f"CTL-{i:03d}", "CONTROL_NAME": r[7], "POLICY_ID": r[4], "REGULATION_ID": r[1],
                     "REQUIREMENT_KEY": r[0], "CLAUSE_ID": f"{r[1]} §{r[2]}", "SECTION_ID": f"{r[4]} §{r[5]}"})
    for j, (pid, rid, name) in enumerate(EXTRA_CONTROLS, len(REQUIREMENTS) + 1):
        rows.append({"CONTROL_ID": f"CTL-{j:03d}", "CONTROL_NAME": name, "POLICY_ID": pid, "REGULATION_ID": rid,
                     "REQUIREMENT_KEY": None, "CLAUSE_ID": None, "SECTION_ID": None})
    return pd.DataFrame(rows)


def _tests(controls: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(SEED)
    out, n = [], 0
    for c in controls.itertuples():
        gap = c.REQUIREMENT_KEY in GAPS
        owner = OWNERS[int(c.CONTROL_ID[-3:]) % len(OWNERS)]
        for q_i, q in enumerate(QUARTERS):
            for bu in BUSINESS_UNITS:
                n += 1
                sample = rng.choice([10, 15, 20, 25, 30])
                p_fail = (0.30 + 0.08 * q_i) if gap else 0.05
                if bu == "Payments" and c.REQUIREMENT_KEY == "INCIDENT_NOTIFY":
                    p_fail += 0.15
                failed = rng.random() < p_fail
                exc = rng.randint(1, max(2, sample // 5)) if failed else 0
                out.append({"TEST_ID": f"T{n:05d}", "CONTROL_ID": c.CONTROL_ID, "CONTROL_NAME": c.CONTROL_NAME,
                            "POLICY_ID": c.POLICY_ID, "REGULATION_ID": c.REGULATION_ID, "BUSINESS_UNIT": bu,
                            "QUARTER": q, "QUARTER_END": QUARTER_END[q], "OWNER": owner, "SAMPLE_SIZE": sample,
                            "EXCEPTIONS": exc, "RESULT": "FAIL" if failed else "PASS"})
    return pd.DataFrame(out)


def generate() -> dict[str, pd.DataFrame]:
    regs, clauses = _regulations()
    pols, sections = _policies()
    controls = _controls()
    return {"REGULATIONS": regs, "REG_CLAUSES": clauses, "POLICIES": pols, "POLICY_SECTIONS": sections,
            "CONTROLS": controls, "CONTROL_TESTS": _tests(controls)}


if __name__ == "__main__":
    t = generate()
    for k, v in t.items():
        print(f"{k:16s} {len(v):5d}")
    ct = t["CONTROL_TESTS"]
    print("fail rate", round((ct.RESULT == "FAIL").mean(), 3))
    print(ct[ct.RESULT == "FAIL"].groupby(["QUARTER", "BUSINESS_UNIT"]).size().unstack())
