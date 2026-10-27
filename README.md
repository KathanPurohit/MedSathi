# MedSaathi (મેડસાથી / मेडसाथी) 🩺💊

> **Privacy-First Rx & Lab Simplifier with PMBJP Jan Aushadhi Generic Savings & Multilingual Family Audio Notes**

MedSaathi empowers patients and elderly family members by decoding handwritten doctor prescriptions and complex lab reports into plain language, generating audio notes in **Gujarati**, **Hindi**, and **English**, mapping brand-name medications to affordable government **Jan Aushadhi (PMBJP)** generic alternatives, and exporting 1-tap phone calendar alarms.

---

## 🌟 Key Features

- 🛡️ **Dual-Layer Privacy Shield**:
  - Touch-canvas redactor: black out patient names directly before upload.
  - Client-side sanitization guarantees zero-PII transmission.
- 👁️ **Vision AI Medical Decoding**:
  - Powered by Google Gemini 2.5 Flash.
  - Automatically translates medical shorthand (OD, BD, TDS, AC, PC, HS) into visual morning, afternoon, and night dose slots.
  - Detects potential dietary and drug clashes (e.g., taking thyroid/calcium with milk or chai).
- 💰 **Jan Aushadhi Generic Bill Cutter**:
  - Matches active chemical salts against the official Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP) catalog.
  - Computes exact monthly rupee savings per prescription.
- 👵 **Grandparent-Friendly Spoken Audio Notes**:
  - Converts translated summaries into 20-second caring voice notes in Gujarati, Hindi, or English via TTS.
  - 1-tap native WhatsApp family sharing.
- ⏰ **1-Tap Medication Calendar Alarms**:
  - Generates RFC 5545 `.ics` files that immediately set recurring reminders on native iOS and Android calendars.

---

## 📁 Repository Structure

```
MedSathi/
├── frontend/                     # Next.js 16 (App Router, Tailwind CSS, TypeScript)
│   ├── public/manifest.json      # PWA Configuration
│   └── src/
│       ├── components/           # Mobile-first accessible UI cards
│       ├── config/               # Centralized API endpoints
│       ├── services/             # Analysis, ICS calendar, and WhatsApp sharing
│       └── types/                # Strict TypeScript response contracts
└── backend/                      # FastAPI Python Service
    ├── config/                   # Pydantic Settings & environment loader
    ├── generic_matcher/          # PMBJP CSV catalog & fuzzy salt matcher
    ├── schemas/                  # Pydantic response models
    ├── utilities/                # TTS audio generator & ICS alarm builder
    ├── vision_ai/                # Gemini 2.5 Flash Vision AI extractor
    ├── main.py                   # FastAPI REST API
    └── requirements.txt          # Python dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18+ & npm
- **Python**: 3.10+ (Python 3.11 recommended)
- **Google AI Studio Gemini API Key** ([Get one here](https://aistudio.google.com/))

### 2. Backend Setup

```bash
cd backend

# Setup Python virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY

# Start backend server (runs at http://localhost:8000)
uvicorn main:app --reload --port 8000
```

Interactive API documentation will be accessible at: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Configure environment
cp .env.local.example .env.local

# Run Next.js development server (runs at http://localhost:3000)
npm run dev
```

Open `http://localhost:3000` on your desktop or mobile browser.

---

## 🔒 Privacy & Safety Disclaimer

MedSaathi is built as an assistive educational and financial aid tool for families. It does not provide medical diagnosis or replace consultation with a qualified medical professional. Always verify generic salt substitutions with a licensed pharmacist or physician before switching medications.
