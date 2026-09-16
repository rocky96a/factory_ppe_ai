import os
import cv2
import time
import threading
from datetime import datetime

from config import Config
from cameras.stream import CameraStream

from ai.tracker import PersonTracker
from ai.helmet_detector import HelmetDetector
from ai.person_helmet import associate_helmets
from ai.violation_engine import ViolationEngine

from database.db import add_violation


# =============================================================
# EMAIL MODULE
# =============================================================

try:
    from api.email_alert import send_violation_email

    EMAIL_MODULE_AVAILABLE = True

    print(
        "[EMAIL] Email module loaded"
    )

except Exception as exc:

    print(
        f"[EMAIL] Module unavailable: {exc}"
    )

    send_violation_email = None
    EMAIL_MODULE_AVAILABLE = False


class CameraProcessor:

    def __init__(
        self,
        camera_id,
        name,
        location,
        stream_url
    ):

        self.camera_id = camera_id
        self.name = name
        self.location = location
        self.stream_url = stream_url

        # ---------------------------------------------------------
        # CAMERA STATE
        # ---------------------------------------------------------

        self.running = False
        self.thread = None

        # Latest annotated frame
        self.latest_frame = None

        # Latest people information
        self.latest_persons = []

        # Thread lock
        self.lock = threading.Lock()

        # ---------------------------------------------------------
        # PERSON TRACKER
        # ---------------------------------------------------------

        self.tracker = PersonTracker(
            Config.PERSON_MODEL,
            Config.DETECTION_CONFIDENCE
        )

        # ---------------------------------------------------------
        # HELMET DETECTOR
        # ---------------------------------------------------------

        self.helmet_detector = HelmetDetector(
            Config.HELMET_MODEL,
            Config.HELMET_CONFIDENCE
        )

        # ---------------------------------------------------------
        # VIOLATION ENGINE
        # ---------------------------------------------------------

        self.violation_engine = ViolationEngine(
            Config.VIOLATION_CONFIRM_FRAMES,
            Config.VIOLATION_COOLDOWN_SECONDS
        )

        print(
            f"[CAMERA] Created {self.camera_id} "
            f"| name={self.name} "
            f"| location={self.location} "
            f"| source={self.stream_url}"
        )

    # =============================================================
    # START
    # =============================================================

    def start(self):

        if self.running:

            print(
                f"[CAMERA] {self.camera_id} already running"
            )

            return

        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )

        self.thread.start()

        print(
            f"[CAMERA] {self.camera_id} started"
        )

    # =============================================================
    # STOP
    # =============================================================

    def stop(self):

        self.running = False

        print(
            f"[CAMERA] {self.camera_id} stopping..."
        )

        if self.thread is not None:

            self.thread.join(
                timeout=3
            )

        print(
            f"[CAMERA] {self.camera_id} stopped"
        )

    # =============================================================
    # WORKER
    # =============================================================

    def _worker(self):

        # ---------------------------------------------------------
        # Convert webcam "0" to integer 0
        # ---------------------------------------------------------

        source = self.stream_url

        try:

            source = int(source)

        except (
            ValueError,
            TypeError
        ):

            pass

        print(
            f"[CAMERA] {self.camera_id} "
            f"using source={source!r}"
        )

        stream = CameraStream(source)

        while self.running:

            # =====================================================
            # CONNECT CAMERA
            # =====================================================

            if not stream.is_opened():

                print(
                    f"[CAMERA] {self.camera_id}: "
                    f"connecting..."
                )

                stream.reconnect()

                if not stream.is_opened():

                    print(
                        f"[CAMERA] {self.camera_id}: "
                        f"connection failed"
                    )

                    time.sleep(2)

                    continue

                print(
                    f"[CAMERA] {self.camera_id}: "
                    f"connected"
                )

            # =====================================================
            # READ FRAME
            # =====================================================

            success, frame = stream.read()

            if not success:

                print(
                    f"[CAMERA] {self.camera_id}: "
                    f"stream lost"
                )

                stream.reconnect()

                time.sleep(1)

                continue

            # =====================================================
            # PERSON TRACKING
            # =====================================================

            try:

                persons = self.tracker.track(
                    frame
                )

            except Exception as exc:

                print(
                    f"[AI ERROR] Person tracking: {exc}"
                )

                persons = []

            # =====================================================
            # HELMET DETECTION
            # =====================================================

            try:

                helmet_detections = (
                    self.helmet_detector.detect(
                        frame
                    )
                )

            except Exception as exc:

                print(
                    f"[AI ERROR] Helmet detection: {exc}"
                )

                helmet_detections = []

            # =====================================================
            # PERSON ↔ HELMET ASSOCIATION
            # =====================================================

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
                    f"[AI ERROR] "
                    f"Helmet association: {exc}"
                )

                # IMPORTANT:
                # Do not destroy person tracking if
                # helmet association fails.

                associated = []

                for person in persons:

                    result = dict(person)

                    result["helmet"] = None
                    result["helmet_status"] = "UNKNOWN"
                    result["helmet_confidence"] = 0.0
                    result["helmet_bbox"] = None

                    associated.append(
                        result
                    )

            # =====================================================
            # STORE CURRENT PEOPLE
            # =====================================================

            with self.lock:

                self.latest_persons = [
                    dict(person)
                    for person in associated
                ]

            # =====================================================
            # VIOLATION ENGINE
            # =====================================================

            try:

                violations = (
                    self.violation_engine.process(
                        self.camera_id,
                        associated
                    )
                )

            except Exception as exc:

                print(
                    f"[AI ERROR] "
                    f"Violation engine: {exc}"
                )

                violations = []

            # =====================================================
            # HANDLE ALL VIOLATIONS
            # =====================================================

            if violations:

                print(
                    f"[ALERT] "
                    f"{self.camera_id}: "
                    f"{len(violations)} "
                    f"violation(s)"
                )

            for violation in violations:

                try:

                    self._save_violation(
                        frame,
                        violation
                    )

                except Exception as exc:

                    print(
                        f"[ERROR] "
                        f"Save violation: {exc}"
                    )

            # =====================================================
            # DRAW
            # =====================================================

            try:

                annotated = self._draw(
                    frame,
                    associated
                )

            except Exception as exc:

                print(
                    f"[AI ERROR] Drawing: {exc}"
                )

                annotated = frame.copy()

            # =====================================================
            # STORE LIVE FRAME
            # =====================================================

            with self.lock:

                self.latest_frame = (
                    annotated.copy()
                )

        # =========================================================
        # RELEASE CAMERA
        # =========================================================

        stream.release()

        print(
            f"[CAMERA] {self.camera_id}: "
            f"worker exited"
        )

    # =============================================================
    # DRAW
    # =============================================================

    def _draw(
        self,
        frame,
        persons
    ):

        output = frame.copy()

        helmet_count = 0
        no_helmet_count = 0
        unknown_count = 0

        # =========================================================
        # DRAW EVERY PERSON
        # =========================================================

        for person in persons:

            bbox = person.get(
                "bbox"
            )

            if not bbox:
                continue

            x1, y1, x2, y2 = bbox

            track_id = person.get(
                "track_id"
            )

            status = person.get(
                "helmet_status",
                "UNKNOWN"
            )

            confidence = float(
                person.get(
                    "helmet_confidence",
                    0.0
                ) or 0.0
            )

            # -----------------------------------------------------
            # HELMET
            # -----------------------------------------------------

            if status == "HELMET":

                helmet_count += 1

                label = (
                    f"ID {track_id} | "
                    f"HELMET "
                    f"{confidence:.0%}"
                )

                color = (
                    0,
                    255,
                    0
                )

            # -----------------------------------------------------
            # NO HELMET
            # -----------------------------------------------------

            elif status == "NO_HELMET":

                no_helmet_count += 1

                label = (
                    f"ID {track_id} | "
                    f"NO HELMET "
                    f"{confidence:.0%}"
                )

                color = (
                    0,
                    0,
                    255
                )

            # -----------------------------------------------------
            # UNKNOWN
            # -----------------------------------------------------

            else:

                unknown_count += 1

                label = (
                    f"ID {track_id} | "
                    f"PERSON"
                )

                color = (
                    180,
                    180,
                    180
                )

            # -----------------------------------------------------
            # PERSON BOX
            # -----------------------------------------------------

            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            # -----------------------------------------------------
            # LABEL BACKGROUND
            # -----------------------------------------------------

            label_y1 = max(
                y1 - 32,
                0
            )

            label_y2 = y1

            cv2.rectangle(
                output,
                (x1, label_y1),
                (x2, label_y2),
                color,
                -1
            )

            # -----------------------------------------------------
            # LABEL
            # -----------------------------------------------------

            cv2.putText(
                output,
                label,
                (
                    x1 + 5,
                    max(
                        y1 - 10,
                        20
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

            # -----------------------------------------------------
            # DRAW HELMET BOX IF AVAILABLE
            # -----------------------------------------------------

            helmet_bbox = person.get(
                "helmet_bbox"
            )

            if helmet_bbox:

                hx1, hy1, hx2, hy2 = (
                    helmet_bbox
                )

                cv2.rectangle(
                    output,
                    (
                        int(hx1),
                        int(hy1)
                    ),
                    (
                        int(hx2),
                        int(hy2)
                    ),
                    color,
                    2
                )

        # =========================================================
        # CAMERA INFORMATION
        # =========================================================

        cv2.putText(
            output,
            f"{self.camera_id} | {self.location}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        # =========================================================
        # AI LIVE
        # =========================================================

        cv2.putText(
            output,
            "AI LIVE",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2
        )

        # =========================================================
        # PERSON COUNT
        # =========================================================

        cv2.putText(
            output,
            f"PERSONS: {len(persons)}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # =========================================================
        # HELMET COUNT
        # =========================================================

        cv2.putText(
            output,
            f"HELMET: {helmet_count}",
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (0, 255, 0),
            2
        )

        # =========================================================
        # NO HELMET COUNT
        # =========================================================

        cv2.putText(
            output,
            f"NO HELMET: {no_helmet_count}",
            (20, 158),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (0, 0, 255),
            2
        )

        # =========================================================
        # UNKNOWN COUNT
        # =========================================================

        cv2.putText(
            output,
            f"UNKNOWN: {unknown_count}",
            (20, 186),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (200, 200, 200),
            2
        )

        # =========================================================
        # HELMET MODEL STATUS
        # =========================================================

        if self.helmet_detector.available:

            model_text = (
                "HELMET AI: ONLINE"
            )

            model_color = (
                0,
                255,
                0
            )

        else:

            model_text = (
                "HELMET AI: MODEL MISSING"
            )

            model_color = (
                0,
                165,
                255
            )

        cv2.putText(
            output,
            model_text,
            (20, 216),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            model_color,
            2
        )

        # =========================================================
        # EMAIL STATUS
        # =========================================================

        if EMAIL_MODULE_AVAILABLE:

            email_text = (
                "EMAIL ALERT: READY"
            )

            email_color = (
                0,
                255,
                0
            )

        else:

            email_text = (
                "EMAIL ALERT: OFFLINE"
            )

            email_color = (
                0,
                165,
                255
            )

        cv2.putText(
            output,
            email_text,
            (20, 244),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            email_color,
            2
        )

        return output

    # =============================================================
    # SAVE VIOLATION
    # =============================================================

    def _save_violation(
        self,
        frame,
        violation
    ):

        # ---------------------------------------------------------
        # Evidence directory
        # ---------------------------------------------------------

        os.makedirs(
            Config.EVIDENCE_DIR,
            exist_ok=True
        )

        # ---------------------------------------------------------
        # Timestamp
        # ---------------------------------------------------------

        timestamp = datetime.now()

        timestamp_text = (
            timestamp.strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )

        # ---------------------------------------------------------
        # Tracking ID
        # ---------------------------------------------------------

        tracking_id = violation.get(
            "track_id"
        )

        # ---------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------

        confidence = float(
            violation.get(
                "confidence",
                0.0
            ) or 0.0
        )

        # ---------------------------------------------------------
        # Filename
        # ---------------------------------------------------------

        filename = (
            f"{self.camera_id}_"
            f"ID_{tracking_id}_"
            f"{timestamp_text}.jpg"
        )

        evidence_path = os.path.join(
            Config.EVIDENCE_DIR,
            filename
        )

        # ---------------------------------------------------------
        # SAVE PHOTO
        # ---------------------------------------------------------

        saved = cv2.imwrite(
            evidence_path,
            frame
        )

        if not saved:

            print(
                f"[ERROR] Could not save evidence: "
                f"{evidence_path}"
            )

            return

        print(
            f"[EVIDENCE] Saved: "
            f"{evidence_path}"
        )

        # =========================================================
        # DATABASE
        # =========================================================

        violation_id = add_violation(
            camera_id=self.camera_id,
            location=self.location,
            tracking_id=tracking_id,
            detection=violation.get(
                "detection",
                "NO_HELMET"
            ),
            confidence=confidence,
            evidence_path=evidence_path
        )

        print(
            f"[VIOLATION] "
            f"DB ID={violation_id} "
            f"| Camera={self.camera_id} "
            f"| Location={self.location} "
            f"| Tracking ID={tracking_id} "
            f"| Confidence={confidence:.2%}"
        )

        # =========================================================
        # AUTOMATIC EMAIL
        # =========================================================

        if (
            EMAIL_MODULE_AVAILABLE
            and send_violation_email is not None
        ):

            email_thread = threading.Thread(
                target=self._send_email_background,
                kwargs={
                    "violation_id": violation_id,
                    "tracking_id": tracking_id,
                    "confidence": confidence,
                    "evidence_path": evidence_path
                },
                daemon=True
            )

            email_thread.start()

            print(
                f"[EMAIL] Task started "
                f"| Violation={violation_id} "
                f"| ID={tracking_id}"
            )

        else:

            print(
                "[EMAIL] Email module not available"
            )

    # =============================================================
    # BACKGROUND EMAIL
    # =============================================================

    def _send_email_background(
        self,
        violation_id,
        tracking_id,
        confidence,
        evidence_path
    ):

        try:

            result = send_violation_email(
                violation_id=violation_id,
                camera_id=self.camera_id,
                location=self.location,
                tracking_id=tracking_id,
                confidence=confidence,
                evidence_path=evidence_path
            )

            if result:

                print(
                    f"[EMAIL] SENT | "
                    f"Violation={violation_id} | "
                    f"Camera={self.camera_id} | "
                    f"ID={tracking_id}"
                )

            else:

                print(
                    f"[EMAIL] FAILED | "
                    f"Violation={violation_id} | "
                    f"Camera={self.camera_id} | "
                    f"ID={tracking_id}"
                )

        except Exception as exc:

            print(
                f"[EMAIL] ERROR | "
                f"Violation={violation_id} | "
                f"Camera={self.camera_id} | "
                f"ID={tracking_id} | "
                f"{exc}"
            )

    # =============================================================
    # GET FRAME
    # =============================================================

    def get_frame(self):

        with self.lock:

            if self.latest_frame is None:

                return None

            return (
                self.latest_frame.copy()
            )

    # =============================================================
    # GET PEOPLE
    # =============================================================

    def get_people(self):

        with self.lock:

            return [
                dict(person)
                for person in self.latest_persons
            ]

    # =============================================================
    # GET STATUS
    # =============================================================

    def get_status(self):

        with self.lock:

            people = [
                dict(person)
                for person in self.latest_persons
            ]

        helmet_count = 0
        no_helmet_count = 0
        unknown_count = 0

        # =========================================================
        # COUNT EVERY PERSON
        # =========================================================

        for person in people:

            status = person.get(
                "helmet_status",
                "UNKNOWN"
            )

            if status == "HELMET":

                helmet_count += 1

            elif status == "NO_HELMET":

                no_helmet_count += 1

            else:

                unknown_count += 1

        # =========================================================
        # STATUS
        # =========================================================

        return {

            "camera_id": self.camera_id,

            "name": self.name,

            "location": self.location,

            "running": self.running,

            "person_count": len(
                people
            ),

            "helmet_count": helmet_count,

            "no_helmet_count": no_helmet_count,

            "unknown_count": unknown_count,

            "helmet_model_available": (
                self.helmet_detector.available
            ),

            "email_module_available": (
                EMAIL_MODULE_AVAILABLE
            ),

            "people": people

        }