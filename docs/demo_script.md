\# KisanSetu Demo Script

\## Pune Agri Hackathon 2026



\*\*Team:\*\* Faiza Bagban + Sakshi Kolhe  

\*\*Duration:\*\* \~8 minutes  

\*\*URL:\*\* https://kisansetu-prod-backend.onrender.com (staging) or localhost



\---



\## 1. Login (30s)

\- Open app → Login page

\- Login as: `admin@kisansetu.gov` / `password123`

\- Show role-based nav appears for Admin



\## 2. Farmer Portal (1min)

\- Show live weather data (temp, humidity, rainfall)

\- Click "Predict Crop Risk" → AI shows LOW/HIGH risk with confidence

\- Show "Check Eligibility" → scheme matching



\## 3. Officer Verification Console (2min)

\- Go to Officer Desk

\- Upload `clean.jpg` → click "Start AI Scan"

\- Show OCR extraction: \*\*Ramesh Patil, MH-1234, XXXX-XXXX-9012\*\*

\- All 3 fields → \*\*AUTO-VERIFIED, 95% confidence\*\*

\- Click "Approve \& Sync to Backend"



\## 4. Grievance Intelligence Portal (1min)

\- Go to Grievances

\- Type: "Canal irrigation water hasn't reached farms in Pune for 3 months"

\- Submit → AI classifies, routes to District Agriculture Officer

\- Show lifecycle tracker: Submitted → Processing



\## 5. Crop Risk Intelligence Map (2min)

\- Go to Risk Map

\- Show Maharashtra map with district markers (red = high risk)

\- Show District Insights sidebar: Nashik, Aurangabad NDVI drops

\- Scroll down → NDVI Bar Chart (real satellite data)

\- Show Audit Intelligence Trail



\## 6. Intelligence Report (1min)

\- Go to Intelligence

\- Show Dhurandhar Report — 6 metrics across all districts

\- Show Land Fragmentation map + charts

\- Highlight CRITICAL ALERT banner



\## Key Talking Points

\- \*\*Real data:\*\* IMD 2024 rainfall, NASA POWER soil moisture, NDVI satellite

\- \*\*Multilingual OCR:\*\* English + Marathi + Hindi documents

\- \*\*Security:\*\* JWT auth, rate limiting, RBAC, audit logging

\- \*\*CI/CD:\*\* GitHub Actions, staging on Render

\- \*\*46 tests passing\*\*, accessibility score 93

