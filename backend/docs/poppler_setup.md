# Poppler Setup (Windows) — Required for PDF OCR

`pdf2image` (used by `idp.py`) needs Poppler binaries to convert PDFs to images.

## Install Steps

1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/latest
2. Pick the `Release-xx.xx.x-0.zip` file (~30MB, not Source code)
3. Extract to `C:\poppler\`
4. Add to PATH — **one-time per terminal session** (no admin needed):
   ```powershell
   $env:Path += ";C:\poppler\poppler-26.02.0\Library\bin"
   ```
5. Verify:
   ```powershell
   where.exe pdftoppm
   ```

## Important

**Uvicorn must be started AFTER setting PATH** — otherwise PDF requests return 500.
Always run the PATH line before `uvicorn main:app --reload`.

Permanent fix (needs admin): add `C:\poppler\poppler-26.02.0\Library\bin` to System PATH via
Windows Settings → System → Advanced → Environment Variables.

## Verified Working

| File | Result |
|------|--------|
| Form_1-MR.pdf | 200 OK, Marathi Aadhaar form extracted |
| marathi.pdf | 200 OK |
| sample.pdf | 200 OK |