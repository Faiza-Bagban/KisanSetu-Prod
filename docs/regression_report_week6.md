\# Week 6 Day 3 — Regression Test Report

\*\*Date:\*\* 2026-07-26  

\*\*Tester:\*\* Sakshi



\## Full Suite Result



38 passed, 9 skipped, 0 failed — 80.10s





\## Regression Confirmed Clean

All fixes from Week 6 Day 1-2 verified stable:

\- lifespan migration — no deprecation warnings

\- Route registration — 39 routes confirmed

\- Ollama skip guard — 5 eligibility tests correctly skipped

\- Rate limit bypass — auth tests no longer rate-limited in test env



\## Skipped (9) — All Expected

\- 5 eligibility AI tests (Ollama/GPU — Faiza's machine)

\- 2 auth rate-limit tests (intentional skip when limit hit)

\- 2 other skips



\## Status: STABLE ✅

