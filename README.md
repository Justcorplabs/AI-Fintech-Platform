# AI Fintech Intelligence Platform

**JustCorp Labs** | Financial Fraud Detection + AI Recruitment & CV Screening

## Modules
- **Fraud Detection** — XGBoost + LightGBM ensemble with SHAP explainability (Joe)
- **CV Screening** — spaCy NLP + Groq LLaMA 3 candidate scoring (Partner)

## Quick Start

### Prerequisites
- Python 3.11+, Node 18+, Docker, PostgreSQL 15

### Backend
```bash
cd backend
cp .env.example .env        # fill in your values
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

### Docker (recommended)
```bash
cp backend/.env.example backend/.env
docker-compose up --build
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

## Project Structure
```
ai-fintech-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # auth, fraud, recruitment endpoints
│   │   ├── core/           # config, security (JWT)
│   │   ├── db/             # SQLAlchemy engine + session
│   │   ├── models/         # DB models (User, Transaction, CVApplication)
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/
│   │       ├── fraud/      # ML predictor (Joe)
│   │       └── recruitment/# CV parser (Partner)
│   └── main.py
├── frontend/               # React + Vite (Partner)
├── docker-compose.yml
└── README.md
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Get JWT token |
| POST | /api/v1/fraud/predict | Score a transaction |
| GET  | /api/v1/fraud/transactions | List transactions |
| GET  | /api/v1/fraud/stats | Dashboard stats |
| POST | /api/v1/recruitment/jobs | Create job post |
| POST | /api/v1/recruitment/upload-cv/{job_id} | Upload & parse CV |
| GET  | /api/v1/recruitment/applications/{job_id} | Get ranked applicants |

## Roadmap
- **Phase 1** (Weeks 1-4): Setup & scaffold ← You are here
- **Phase 2** (Weeks 5-12): Train fraud ML model, build CV NLP pipeline
- **Phase 3** (Weeks 13-20): SHAP dashboard, demo site, Upwork launch

## Team
- **Joe (TJ)** — ML, backend, fraud detection, deployment
- **Partner** — NLP, frontend, CV screening module
