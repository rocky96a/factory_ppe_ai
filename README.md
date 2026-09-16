# Factory PPE AI

Real-time factory CCTV PPE / helmet detection system.

## Architecture

CCTV / RTSP
    ↓
YOLO
    ↓
Person Tracking
    ↓
Helmet Detection
    ↓
Person/Helmet Association
    ↓
Violation Engine
    ↓
Evidence
    ↓
SQLite
    ↓
Flask Dashboard

## Run

```bash
source .venv/bin/activate
python app.py