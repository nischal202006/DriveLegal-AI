# 🛡️ DriveLegal AI — Road Safety Legal Assistant

> **IIT Madras Road Safety Hackathon 2026** — AI-powered chatbot for Indian traffic rules, violations, and penalties

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Structure](#database-structure)
- [Team & Work Division](#team--work-division)
- [Evaluation Criteria Mapping](#evaluation-criteria-mapping)

---

## 🎯 Overview

**DriveLegal AI** is an AI-powered legal chatbot that provides **location-specific information** on Indian traffic laws, violations, fines, and enforcement procedures. It integrates national rules (Motor Vehicles Amendment Act, 2019) with **state and local enforcement regulations** to help citizens easily understand traffic regulations, calculate challans, and promote road safety.

### Problem Statement
Citizens often lack easy access to clear, location-specific information about traffic laws, penalties, and enforcement procedures. Fine structures vary significantly across Indian states, creating confusion. DriveLegal AI solves this by providing a centralized, AI-powered platform.

---

## ✨ Features

### 1. 🧠 Intelligent Chat Interface
- Natural language understanding with intent detection
- Handles vague queries like "I got challan, what to do?"
- Asks minimal clarifying questions before answering
- Context-aware follow-up conversations

### 2. 📍 Geo-Aware Intelligence
- Automatic browser geolocation detection
- City-to-state mapping for 70+ Indian cities
- State-specific fine calculations
- Coverage for all 28 states and 8 union territories

### 3. 💰 Challan Calculator
- Calculates fines based on:
  - Violation type (25+ types covered)
  - Vehicle type (bike, car, truck, bus, auto, taxi)
  - Location (state-specific overrides)
  - First offense vs repeat offense
- Shows fine breakdown, applicable law section, and additional penalties

### 4. 📖 Legal Explanation Engine
- Explains laws in simple, non-technical language
- Covers: What rule was violated, why it exists, consequences, how to avoid it
- Provides safety advice and preventive tips

### 5. ⚡ Offline Mode
- LocalStorage caching of previous responses
- Fuzzy-match cache lookup for similar queries
- Clear "offline mode" indicator in UI
- Works without internet after initial use

### 6. 🛡️ Safety-First Responses
- Never encourages rule-breaking
- Promotes safe driving practices
- Emergency helpline numbers always accessible
- "If you repeat this violation" warnings

### 7. 📊 Structured Output
- Violation cards with fine amount, section, vehicle type, location
- Confidence indicators (High/Medium/Low)
- Compoundable vs non-compoundable offense marking
- Quick-action suggestion chips

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND                          │
│  ┌──────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ Chat UI  │  │ Geolocation│  │ Offline Cache  │  │
│  │ (HTML/   │  │ (Browser   │  │ (LocalStorage) │  │
│  │  CSS/JS) │  │  API +     │  │                │  │
│  │          │  │  OSM)      │  │                │  │
│  └────┬─────┘  └─────┬──────┘  └───────┬────────┘  │
│       │              │                 │            │
│       └──────────────┼─────────────────┘            │
│                      │ REST API                     │
├──────────────────────┼──────────────────────────────┤
│                   BACKEND                           │
│  ┌──────────┐  ┌─────┴──────┐  ┌────────────────┐  │
│  │ Flask    │  │ NLP Engine │  │ Challan        │  │
│  │ Server   │──│ (Intent +  │──│ Calculator     │  │
│  │ (app.py) │  │  Entity)   │  │                │  │
│  └──────────┘  └─────┬──────┘  └───────┬────────┘  │
│                      │                 │            │
│               ┌──────┴─────────────────┴──────┐     │
│               │     Rules Database            │     │
│               │  (Structured JSON files)      │     │
│               └───────────────────────────────┘     │
│                                                     │
│  ┌────────────────────────────────────────────────┐  │
│  │  📁 data/                                      │  │
│  │  ├── india_national.json  (MV Act 2019)       │  │
│  │  └── india_states.json    (All States + UTs)  │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
hackaton/
├── app.py                    # Flask server (main entry point)
├── nlp_engine.py             # Intent detection & response generation
├── challan_calculator.py     # Fine calculation engine
├── rules_database.py         # Database loader & query functions
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── data/                     # Structured rules database
│   ├── india_national.json   # Motor Vehicles Act 2019 — 25+ violations
│   └── india_states.json     # All 28 states + 8 UTs, 70+ city mappings
│
└── static/                   # Frontend assets
    ├── index.html            # Chat interface
    ├── styles.css            # Premium dark-mode UI with glassmorphism
    └── app.js                # Chat logic, geolocation, offline caching
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.8+** installed
- **pip** package manager

### Steps

```bash
# 1. Clone or navigate to the project directory
cd hackaton

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the server
python app.py

# 4. Open in browser
# Visit http://localhost:5000
```

The app will start at `http://localhost:5000`. Open this URL in your browser.

### Quick Test
After starting the server, try these queries in the chat:
- "Fine for no helmet in Mumbai"
- "What happens if I drive drunk?"
- "Speed limits for bikes"
- "I got a challan, what to do?"

---

## 📡 API Documentation

### `POST /api/chat`
Main chat endpoint. Processes natural language queries.

**Request:**
```json
{
  "message": "Fine for no helmet in Delhi",
  "location": "delhi",
  "session_id": "unique_session_id"
}
```

**Response:**
```json
{
  "text": "🚨 **Riding without Helmet**\n...",
  "data": {
    "type": "violation_result",
    "violation": "Riding without Helmet",
    "applicable_law": "Motor Vehicles Act, Section 194D",
    "fine_amount": "₹1,000",
    "vehicle_type": "Two Wheeler",
    "confidence": "High"
  },
  "suggestion_chips": ["Overspeeding fine", "Drunk driving"]
}
```

### `POST /api/calculate`
Direct challan calculation.

**Request:**
```json
{
  "violation": "no_helmet",
  "vehicle_type": "two_wheeler",
  "state": "delhi",
  "is_repeat": false
}
```

### `GET /api/violations`
List all violation types.

### `GET /api/states`
List all supported states.

### `GET /api/speed-limits?vehicle=car`
Get speed limits for a vehicle type.

### `GET /api/health`
Server health check.

---

## 🗄️ Database Structure

### National Rules (`india_national.json`)
- **25+ violation types** with MV Act sections
- Fine amounts for first and repeat offenses
- Vehicle-type-specific fines
- Additional penalties (imprisonment, licence suspension)
- Safety advice and law explanations
- Speed limits for city/highway/expressway
- Emergency numbers

### State Rules (`india_states.json`)
- **All 28 states and 8 union territories**
- State-specific fine overrides
- Local enforcement rules
- **70+ city-to-state mappings** for geo-aware responses

---

## 👥 Team & Work Division

### Core Team (8 Members)

| Member | Role | Responsibilities | Files Owned |
| :---: | :--- | :--- | :--- |
| **nischal202006** | **Backend Lead & DevOps** | Flask architecture, SQLite schema, JWT Auth, API endpoints. | `app.py`, `wsgi.py` |
| **hemanthkumar2006** | **AI / NLP Engineer** | Gemini 2.0 integration, prompt engineering, AI Camera backend. | `nlp_engine.py` |
| **vineelsaireddy** | **Frontend Lead (UI/UX)** | CSS/Design system, dark/light theme, PWA/Offline mode. | `static/styles.css`, `static/index.html` |
| **Jittu496** | **Location Systems Engineer**| Leaflet Map, hotspots, map UI components. | `static/app.js` (map logic) |
| **Shashank3312** | **Core Logic Engineer** | Challan calculator, state override logic, fallback NLP engine. | `challan_calculator.py` |
| **RiyasShaik** | **Data & Localization Lead** | JSON legal datasets, state mapping, i18n (translations). | `data/*.json`, `rules_database.py` |
| **Chervith-Reddy**| **Safety & Features Dev** | Emergency SOS UI, Dashboard, Safety score animations. | `static/index.html` (panels) |
| **Kowshikh-10** | **Integration & QA** | Testing, E2E bug fixes, README, frontend API wireup. | `README.md`, `static/app.js` |

### 12-Day Development Sprint Timeline (May 1 - May 12, 2026)

| Phase | Days | Focus | Commits Made |
|-------|------|-------|--------------|
| **Phase 1: Foundation** | May 1 - 3 | Project structure, Flask, NLP drafts, UI scaffolding, national database | ~10 commits |
| **Phase 2: Core Features** | May 4 - 7 | API endpoints, chat interface, fine calculations, state-level data, SOS | ~9 commits |
| **Phase 3: Integrations** | May 8 - 10 | DB optimization, PWA implementation, offline fallback, map hotspots | ~8 commits |
| **Phase 4: Polish & QA** | May 11 - 12 | E2E testing, WSGI/SSL setup, Gemini prompt refinement, UI responsiveness | ~8 commits |

---

## 📊 Evaluation Criteria Mapping

| Criteria | How We Score | Evidence |
|----------|-------------|---------|
| **Legal accuracy & regulatory coverage** | ✅ Complete MV Act 2019 database with 25+ violations, all sections referenced, first/repeat offense amounts | `data/india_national.json` |
| **Challan calculator functionality & correctness** | ✅ Structured calculator with vehicle type, state, repeat offense, per-extra-passenger/tonne charges | `challan_calculator.py` |
| **Information integration across countries** | ✅ All 28 Indian states + 8 UTs covered with state-specific overrides, 70+ city-to-state mappings | `data/india_states.json` |
| **User interface & accessibility** | ✅ Premium glassmorphism UI, dark mode, animations, responsive mobile-first, keyboard accessible, suggestion chips | `static/` |

### Bonus Features
- 🌐 **Geo-aware** — Auto-detects user city/state via browser geolocation
- ⚡ **Offline capable** — LocalStorage caching with fuzzy matching
- 🤖 **Conversational** — Context-aware follow-up questions
- 📱 **Mobile responsive** — Works on all screen sizes
- 🛡️ **Safety-first** — Every response includes safety advice

---

## 📜 License

This project is built for the **IIT Madras Road Safety Hackathon 2026** organized by the Centre of Excellence for Road Safety (CoERS), RBG Labs.

---

## 🙏 Acknowledgments

- **Motor Vehicles (Amendment) Act, 2019** — Ministry of Road Transport and Highways, Government of India
- **Parivahan Sewa** — parivahan.gov.in
- **IIT Madras CoERS** — For organizing this hackathon
- **OpenStreetMap Nominatim** — For reverse geocoding API

---

> **"Every response we generate has the potential to save a life on the road."**
> — DriveLegal AI Team
