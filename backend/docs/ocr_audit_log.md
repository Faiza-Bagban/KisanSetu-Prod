# OCR Audit Log — `backend/modules/idp.py`
**Auditor:** Sakshi
**Task:** Week 1, Day 3 — log all known OCR failure cases from code comments

Failure cases below pulled straight from the module's own fix-history comments (v1 → v3), listed oldest to newest.

## Base fixes (v1)
1. **UnboundLocalError** — `candidate` var was scoped wrong inside name-match block.
2. **Broken Devanagari regex** — old regex didn't cover full Unicode block; fixed to use `\u0900-\u097F` everywhere.
3. **Low OCR accuracy** — added 2× upscale + Otsu/adaptive dual preprocessing + multi-PSM voting.
4. **Missing Marathi field patterns** — नाव, जन्म तारीख, वडिलांचे नाव, जात, गोत्र etc. not matched before.
5. **Poor PDF quality** — PDFs rendered too low-res; fixed via `convert_from_path` at 250 DPI.
6. **Table/land-record extraction failing** — needed pixel-aligned row grouping + KV parser.

## v2 fixes (from live test run)
7. **Degraded separator not matched** — OCR sometimes reads `:` as `.` or `;` on degraded scans; patterns now accept all four (`:` `-` `.` `;`).
8. **Marathi name fallback missing** — when regex fails on name field, no fallback existed; now derives name from KV pairs.
9. **False-positive address** — single-word label-only values (like the field label itself) were wrongly accepted as address.
10. **kv_pairs UnboundLocalError** — fallback blocks referenced `kv_pairs` before it was defined; moved after step 5.

## v3 fixes (from live test run #2)
11. **Wrong name pulled from garbled family-key** (seen on `marathi_image` test file) — OCR mangled "आईचे नाव" (mother's name) into "ange नाव", which still matched the generic नाव/name check and incorrectly overwrote the subject's own name with the mother's.
    - **Root cause:** no check on what the key started with.
    - **Fix:** a standalone नाव/Name key must start with a Devanagari character, or be a plain ASCII word — never a Latin prefix followed by a Devanagari word.
12. **Address false-positive on "काळजी"** (seen on `Form_1-MR` test file) — the label word "काळजी" is exactly 5 Unicode characters, which slipped past the old `{5,}` minimum-length guard.
    - **Fix:** address is now cleared post-extraction if it has fewer than 2 words (a real address is never a single word).

## Known test assets referenced in module
`clean.jpg`, `partial.jpg`, `degraded.jpg`, `variation.jpg`, `fraud.jpg`, `sample.pdf`, `marathi.pdf`, `Form_1-MR.pdf`, `marathi_image.jpeg` — these are the existing manual test cases used to surface bugs #11 and #12 above; should be reused as regression cases going forward.

## Open risk areas (not yet flagged as fixed bugs, but worth watching in Week 2 OCR polish)
- Reliance on `Counter.most_common` surname inference (step 5c) is a last-resort heuristic, not a real extraction — could misassign a surname if family fields are also garbled.
- Only Marathi + English + Hindi-adjacent Devanagari fields handled; no explicit Hindi-specific field synonyms yet (separate task, Week 1 Day 4 — Hindi field-label config).
- `is_valid_name` requires ≥2 tokens — will reject genuinely single-word names, if any exist in real data.