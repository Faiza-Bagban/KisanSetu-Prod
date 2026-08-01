# Week 2 Day 4 — Dual-Script OCR Test Results
**Tester:** Sakshi  
**Date:** 2026-07-22

## Test Summary

All four script/format combinations tested against `/api/idp/extract` endpoint.

| File | Detected Script | Lang Pack | HTTP Status | Notes |
|------|----------------|-----------|-------------|-------|
| `clean.jpg` | `latin` | `eng` | 200 ✅ | Name, land_id, Aadhaar all extracted. db_match=100. AUTO-VERIFIED. |
| `marathi_image.jpeg` | `marathi` | `eng+mar` | 200 ✅ | Biodata form. Family fields extracted. inferred_surname correct. |
| `hindi.webp` | `hindi` | `eng+hin` | 200 ✅ | Voter registration form. Hindi KV pairs extracted correctly. |
| `Form_1-MR.pdf` | `marathi` | `eng+mar` | 200 ✅ | Marathi Aadhaar PDF. Table data extracted. |
| `farmer info.png` | `marathi` | `eng+mar` | 200 ✅ | Bilingual farm doc. District/taluka extracted. |

## Issues Found

1. **Poppler not in system PATH** — PDF requests return 500 unless Poppler PATH set before uvicorn starts.
   Fix documented in `backend/docs/poppler_setup.md`.

2. **PDF Aadhaar field extraction null** — `Form_1-MR.pdf` returns null for name/land_id/aadhaar.
   Root cause: form uses table layout, fields not in `Label : Value` format idp.py expects.
   → Flagged for Week 3 (table-layout PDF extraction improvement).

3. **`farmer info.png` name flagged** — extracted name includes extra tokens from garbled OCR line.
   db_match=5, flagged=true. Expected for low-quality scan.
   → Existing known limitation, not regression.

## Conclusion

Script auto-detect (Day 1) + Hindi pattern wiring (Day 2) confirmed working across all three scripts.
No regressions on existing Marathi/English test cases.