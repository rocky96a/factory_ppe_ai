import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        "database/factory_ppe.db"
    )

    PERSON_MODEL = os.getenv(
        "PERSON_MODEL",
        "yolo11n.pt"
    )

    HELMET_MODEL = os.getenv(
        "HELMET_MODEL",
        "models/helmet.pt"
    )

    DETECTION_CONFIDENCE = float(
        os.getenv("DETECTION_CONFIDENCE", "0.35")
    )

    HELMET_CONFIDENCE = float(
        os.getenv("HELMET_CONFIDENCE", "0.35")
    )

    VIOLATION_CONFIRM_FRAMES = int(
        os.getenv("VIOLATION_CONFIRM_FRAMES", "5")
    )

    VIOLATION_COOLDOWN_SECONDS = int(
        os.getenv("VIOLATION_COOLDOWN_SECONDS", "30")
    )

    EVIDENCE_DIR = os.getenv(
        "EVIDENCE_DIR",
        "evidence/violations"
    )

    SNAPSHOT_DIR = os.getenv(
        "SNAPSHOT_DIR",
        "evidence/snapshots"
    )