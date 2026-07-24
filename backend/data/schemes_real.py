"""
Real scheme eligibility criteria, sourced from official/verified sources
(researched July 2026). Text-based criteria for LLM reasoning — not
hardcoded numeric thresholds, since most schemes don't actually work
that way.

Only includes schemes that are genuinely individually-applicable with
real, checkable criteria. Excluded from the original 11-scheme list:
- NMSA: policy umbrella, not a direct-apply scheme
- DroughtRelief: not one national scheme — state-specific, only exists
  when a drought is officially declared in specific blocks/districts
- OrganicScheme: redundant with PKVY (same scheme, different name)

NFSM and PKVY are included but flagged as cluster-based, not open
individual applications — the AI should communicate this distinction
rather than reasoning as if they work like PM-KISAN/PMFBY.
"""

REAL_SCHEMES = [
    {
        "id": "PM-KISAN",
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "criteria": """
Eligible: Any landholding farmer family, regardless of land size, whose name
is in official land records.
Excluded categories (NOT eligible even if landholding):
- Institutional landholders (trusts, companies, societies)
- Income-tax payers (paid tax in the previous assessment year)
- Government employees (current or retired), except Group D/Class IV/multi-tasking staff
- Professionals: doctors, engineers, lawyers, chartered accountants, architects
- Pensioners receiving ₹10,000/month or more
- Current/former holders of constitutional posts, ministers, MPs, MLAs, mayors
Benefit: ₹6,000/year in 3 installments via direct bank transfer.
""",
        "documents": ["Aadhaar Card", "Land Ownership Proof", "Bank Passbook"],
    },
    {
        "id": "PMFBY",
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "criteria": """
Eligible: All farmers growing a notified crop in a notified area, with valid
land ownership or tenancy documents. Loanee farmers are automatically covered;
non-loanee farmers can apply voluntarily. Tenant farmers and sharecroppers
are eligible per state norms. No land-size or income cap.
Benefit: Crop insurance — up to 100% loss coverage for notified crops, premium
only 1.5-2% (rest subsidized by government).
""",
        "documents": ["Aadhaar Card", "Crop Details", "Bank Account", "Land Record or Tenancy Proof"],
    },
    {
        "id": "KCC",
        "name": "Kisan Credit Card",
        "criteria": """
Eligible: All farmers (individual or joint) who are owner-cultivators, tenant
farmers, oral lessees, sharecroppers, or SHGs/Joint Liability Groups of farmers.
No income cap. Credit limit is calculated by a formula based on land holding,
crops grown, and scale of finance — not a fixed eligibility cutoff.
Collateral-free up to ₹2 lakh.
Benefit: Revolving credit facility for agricultural needs, 4-7% effective interest.
""",
        "documents": ["Aadhaar Card", "Land Record", "Bank Account", "Passport Photos"],
    },
    {
        "id": "SoilHealthCard",
        "name": "Soil Health Card Scheme",
        "criteria": """
Eligible: All landholding farmers, individual or joint, any land size (no
minimum). Tenant farmers and sharecroppers eligible without owning land.
Small and marginal farmers given priority. Income-tax payers and government
employees are typically excluded per standard scheme norms.
Benefit: Free soil testing every 2 years, with fertilizer/crop recommendations.
""",
        "documents": ["Aadhaar Card", "Land Records (khata khatauni)"],
    },
    {
        "id": "eNAM",
        "name": "National Agriculture Market",
        "criteria": """
Eligible: All farmers, land must be recorded in applicant's name. Free
registration. Income-tax payers and government employees typically excluded
per standard scheme norms. No land-size cap.
Benefit: Online trading platform connecting farmers to mandis nationwide for
better price discovery, direct bank payment.
""",
        "documents": ["Aadhaar Card", "Bank Account", "Land Ownership Certificate or Farmer ID (if required by local APMC)"],
    },
    {
        "id": "PMKSY-PDMC",
        "name": "Pradhan Mantri Krishi Sinchayee Yojana (Per Drop More Crop — micro-irrigation)",
        "criteria": """
Eligible: Indian citizen farmers who own cultivable agricultural land and want
to install drip or sprinkler irrigation. Tenant farmers may be eligible in some
states with proper lease documents. Subsidy capped at 5 hectares per beneficiary.
Subsidy rate: 55% for small/marginal farmers, 45% for other farmers.
Must purchase equipment from state-approved vendors.
Benefit: Subsidy on micro-irrigation (drip/sprinkler) system installation.
""",
        "documents": ["Aadhaar Card", "Land Ownership Proof", "Bank Account"],
    },
    {
        "id": "NFSM",
        "name": "National Food Security Mission",
        "criteria": """
IMPORTANT: This is NOT an open individual-application scheme. Farmers are
selected into district-level demonstration clusters (each cluster covers
~100 hectares) by state agriculture departments, not by direct farmer
application. Seed subsidy assistance is limited to 2 hectares per selected
farmer. Targets rice, wheat, pulses, coarse cereals, commercial crops.
If a farmer profile matches the crop focus, tell them to contact their
District Agriculture Office to inquire about current cluster selection —
do not claim direct eligibility the way PM-KISAN/PMFBY work.
""",
        "documents": ["Contact District Agriculture Office for cluster selection process"],
    },
    {
        "id": "PKVY",
        "name": "Paramparagat Krishi Vikas Yojana (Organic Farming)",
        "criteria": """
IMPORTANT: This is NOT an open individual-application scheme. Farmers must
join or form a cluster of 50+ farmers covering at least 50 acres collectively
to participate — an individual farmer cannot apply alone. Promotes organic
farming through cluster-based certification.
If a farmer is interested, tell them to contact their District Agriculture
Office about joining or forming an organic farming cluster — do not claim
direct individual eligibility.
""",
        "documents": ["Contact District Agriculture Office for cluster formation/joining process"],
    },
]