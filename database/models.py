from dataclasses import dataclass
from typing import Optional


@dataclass
class Camera:
    camera_id: str
    name: str
    location: str
    stream_url: str
    enabled: bool = True


@dataclass
class Violation:
    camera_id: str
    location: str
    tracking_id: Optional[int]
    detection: str
    confidence: float
    evidence_path: str