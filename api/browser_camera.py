import base64
import cv2
import numpy as np
import threading

from flask import Blueprint, jsonify, request

from config import Config
from ai.tracker import PersonTracker
from ai.helmet_detector import HelmetDetector
from ai.person_helmet import associate_helmets
from ai.violation_engine import ViolationEngine


browser_camera_bp = Blueprint(
    "browser_camera",
    __name__,
    url_prefix="/api/browser-camera"
)


# ============================================================
# BROWSER CAMERA AI PROCESSOR
# ============================================================

class BrowserCameraProcessor:

    def __init__(self):

        print("[BROWSER AI] Initializing...")

        self.tracker = PersonTracker(
            Config.PERSON_MODEL,
            Config.DETECTION_CONFIDENCE
        )

        self.helmet_detector = HelmetDetector(
            Config.HELMET_MODEL,
            Config.HELMET_CONFIDENCE
        )

        self.violation_engine = ViolationEngine(
            Config.VIOLATION_CONFIRM_FRAMES,
            Config.VIOLATION_COOLDOWN_SECONDS
        )

        self.lock = threading.Lock()

        print("[BROWSER AI] Ready")


    # ========================================================
    # PROCESS FRAME
    # ========================================================

    def process_frame(self, frame):

        # ----------------------------------------------------
        # PERSON TRACKING
        # ----------------------------------------------------

        try:

            persons = self.tracker.track(frame)

        except Exception as exc:

            print(
                f"[BROWSER AI ERROR] "
                f"Person tracking: {exc}"
            )

            persons = []


        # ----------------------------------------------------
        # HELMET DETECTION
        # ----------------------------------------------------

        try:

            helmet_detections = (
                self.helmet_detector.detect(frame)
            )

        except Exception as exc:

            print(
                f"[BROWSER AI ERROR] "
                f"Helmet detection: {exc}"
            )

            helmet_detections = []


        # ----------------------------------------------------
        # PERSON ↔ HELMET ASSOCIATION
        # ----------------------------------------------------

        try:

            associated = associate_helmets(
                persons,
                helmet_detections,
                model_available=(
                    self.helmet_detector.available
                )
            )

        except Exception as exc:

            print(
                f"[BROWSER AI ERROR] "
                f"Helmet association: {exc}"
            )

            associated = []

            for person in persons:

                result = dict(person)

                result["helmet"] = None
                result["helmet_status"] = "UNKNOWN"
                result["helmet_confidence"] = 0.0
                result["helmet_bbox"] = None

                associated.append(result)


        # ----------------------------------------------------
        # VIOLATION ENGINE
        # ----------------------------------------------------

        try:

            violations = (
                self.violation_engine.process(
                    "BROWSER-CAM",
                    associated
                )
            )

        except Exception as exc:

            print(
                f"[BROWSER AI ERROR] "
                f"Violation engine: {exc}"
            )

            violations = []


        # ----------------------------------------------------
        # RETURN SAFE JSON DATA
        # ----------------------------------------------------

        people = []

        for person in associated:

            people.append({

                "track_id": person.get(
                    "track_id"
                ),

                "bbox": list(
                    person.get(
                        "bbox",
                        ()
                    )
                ),

                "person_confidence": float(
                    person.get(
                        "person_confidence",
                        0.0
                    ) or 0.0
                ),

                "helmet_status": person.get(
                    "helmet_status",
                    "UNKNOWN"
                ),

                "helmet_confidence": float(
                    person.get(
                        "helmet_confidence",
                        0.0
                    ) or 0.0
                ),

                "helmet_bbox": (
                    list(
                        person["helmet_bbox"]
                    )
                    if person.get("helmet_bbox")
                    else None
                )

            })


        return {
            "people": people,

            "person_count": len(
                people
            ),

            "helmet_count": sum(
                1
                for person in people
                if person["helmet_status"]
                == "HELMET"
            ),

            "no_helmet_count": sum(
                1
                for person in people
                if person["helmet_status"]
                == "NO_HELMET"
            ),

            "unknown_count": sum(
                1
                for person in people
                if person["helmet_status"]
                == "UNKNOWN"
            ),

            "violations": violations,

            "helmet_model_available": (
                self.helmet_detector.available
            )
        }


# ============================================================
# SINGLE BROWSER CAMERA SESSION
# ============================================================

browser_processor = BrowserCameraProcessor()


# ============================================================
# HEALTH
# ============================================================

@browser_camera_bp.get("/health")
def browser_camera_health():

    return jsonify({

        "success": True,

        "service": "Browser Camera AI",

        "helmet_model_available": (
            browser_processor
            .helmet_detector
            .available
        )

    })


# ============================================================
# PROCESS FRAME
# ============================================================

@browser_camera_bp.post("/frame")
def process_browser_frame():

    # --------------------------------------------------------
    # Read JSON
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "success": False,

            "error": "JSON body required"

        }), 400


    image_data = data.get(
        "image"
    )

    if not image_data:

        return jsonify({

            "success": False,

            "error": "image field required"

        }), 400


    # --------------------------------------------------------
    # Remove data URL prefix
    # --------------------------------------------------------

    if "," in image_data:

        image_data = (
            image_data.split(
                ",",
                1
            )[1]
        )


    # --------------------------------------------------------
    # Decode base64
    # --------------------------------------------------------

    try:

        image_bytes = base64.b64decode(
            image_data,
            validate=True
        )

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

    except Exception as exc:

        print(
            f"[BROWSER AI ERROR] "
            f"Image decode: {exc}"
        )

        return jsonify({

            "success": False,

            "error": "Invalid image data"

        }), 400


    if frame is None:

        return jsonify({

            "success": False,

            "error": "Could not decode image"

        }), 400


    # --------------------------------------------------------
    # Limit unexpectedly huge frames
    # --------------------------------------------------------

    height, width = frame.shape[:2]

    max_width = 960

    if width > max_width:

        scale = (
            max_width / width
        )

        frame = cv2.resize(
            frame,
            (
                int(width * scale),
                int(height * scale)
            ),
            interpolation=cv2.INTER_AREA
        )


    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    with browser_processor.lock:

        result = (
            browser_processor.process_frame(
                frame
            )
        )


    return jsonify({

        "success": True,

        "width": int(
            frame.shape[1]
        ),

        "height": int(
            frame.shape[0]
        ),

        "result": result

    })
