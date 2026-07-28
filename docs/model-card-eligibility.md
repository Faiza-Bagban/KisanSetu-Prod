# Model Card: AI-Powered Scheme Eligibility Engine

## Overview
Determines farmer eligibility for government agricultural schemes using
LLM reasoning over real, verified scheme criteria — not hardcoded
numeric thresholds.

## Approach
Local LLM (Ollama, Llama 3.1 8B, temperature=0 for reproducibility)
reasons over each scheme's real eligibility text given a farmer's
profile. No fine-tuning — this is prompt-based reasoning over retrieved
scheme documents.

## Why not hardcoded thresholds
Initial research found that most major Indian farmer schemes (PM-KISAN,
PMFBY, KCC) do NOT use simple land-size/income cutoffs — they use
category exclusions (income-tax status, government employment, pension
level) or notification-based rules (notified crop/area). A prior
threshold-based version was replaced after this was discovered to be
producing incorrect eligibility determinations.

## Schemes Covered (8, all individually verified)
PM-KISAN, PMFBY, KCC, Soil Health Card, eNAM, PMKSY-PDMC (fully
individual-apply) — plus NFSM and PKVY (correctly flagged as
cluster-based, not individual-apply; the AI asks for cluster status
rather than falsely claiming eligibility).

## Deliberately Excluded
NMSA, DroughtRelief, OrganicScheme — researched and found to not be
genuine individual-application schemes (policy umbrella, state/event-
declared, or duplicate of PKVY respectively).

## Known Limitations
- Requires Ollama running locally — not available on constrained/free
  hosting tiers without GPU (staging shows a graceful "unavailable"
  message in this case)
- Only 8 schemes currently — real value grows as more schemes/documents
  are added to the knowledge base (RAG architecture supports this)
- Confidence scores are the model's self-reported certainty, not a
  calibrated statistical measure

## Retraining / Updating
No training needed — updating a scheme's criteria means editing
`backend/data/schemes_real.py` directly (text-based, human-readable).