\# Week 8 Day 3 — Staging Test Results

\*\*URL:\*\* https://kisansetu-prod-backend.onrender.com  

\*\*Date:\*\* 2026-07-27



\## Results



| Endpoint | Status | Notes |

|----------|--------|-------|

| POST /auth/login | ✅ 200 | Token returned correctly |

| GET /api/ndvi-summary | ✅ 200 | 1 district returned |

| GET /admin/admin-dashboard | ✅ 200 | District risks returned |

| GET /admin/api/audit-logs | ✅ 200 | Logs returned |

| POST /api/grievance | ❌ 502 | OOM — XLM-RoBERTa too heavy for free tier |

| POST /api/grievance (invalid) | ❌ 502 | Server crashed from above |

| GET /api/ndvi-summary (unauth) | ❌ 502 | Server crashed from above |



\## Notes

\- Free Render tier (\~512MB RAM) cannot handle XLM-RoBERTa inference

\- All Sakshi-owned endpoints (auth, NDVI, dashboard, audit) pass ✅

\- Grievance OOM is Faiza's module — flagged to her

\- Cold start time \~50s on free tier

