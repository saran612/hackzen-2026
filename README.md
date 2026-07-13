# SkinCV

SkinCV is a physiology-first facial skin concern analysis and personalized skincare routine recommendation system. It was built for the **HackZen 2026 Open Challenge** (Computer Vision track).

## Team Details
- **Team Zenin**: 
   - premnath V R
   - saran karthick A
   - Aathirai Yaazhini Thiru

## Tech Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite + TailwindCSS v4 + Lucide Icons
- **Computer Vision**: MediaPipe Face Landmarker Tasks API + OpenCV

## Setup & Running Instructions

### Backend
1. Navigate to `backend`:
   ```bash
   cd backend
   ```
2. Set up virtual environment and install packages:
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```
3. Run the development server (runs on port 8002):
   ```bash
   ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
   ```

### Frontend
1. Navigate to `frontend`:
   ```bash
   cd frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Start Vite dev server (runs on port 3000):
   ```bash
   npm run dev -- --port 3000 --host 0.0.0.0
   ```

## Detailed Documentation
For detailed insights into our computer vision methodology, scoring heuristics, routine recommendation logic, and the skin-tone inclusion design decisions, please refer to [DOCUMENTATION.md](DOCUMENTATION.md).
