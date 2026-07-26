\# Sakshi Module Deployment Checklist

\## Week 7 Day 4



\### Pre-deployment

\- \[ ] `VITE\_API\_BASE` set to staging URL in Vercel env vars

\- \[ ] `SECRET\_KEY` set in Render env vars

\- \[ ] `DATABASE\_URL` set in Render env vars



\### Auth endpoints

\- \[ ] POST `/auth/login` → 200 with token

\- \[ ] POST `/auth/refresh` → 200 with new token

\- \[ ] Rate limit → 429 after 5 attempts



\### OCR/IDP endpoints

\- \[ ] POST `/api/idp/extract` with `clean.jpg` → 200, name extracted

\- \[ ] POST `/api/idp/extract` unauthorized → 401



\### Dashboard endpoints

\- \[ ] GET `/api/ndvi-summary` → 200, districts array

\- \[ ] GET `/admin/admin-dashboard` → 200



\### Grievance endpoints

\- \[ ] POST `/api/grievance` valid text → 200

\- \[ ] POST `/api/grievance` short text → 422



\### Frontend pages

\- \[ ] Login page loads

\- \[ ] Farmer portal loads data

\- \[ ] Officer dashboard loads

\- \[ ] Admin map loads with NDVI chart

\- \[ ] Grievance page loads

