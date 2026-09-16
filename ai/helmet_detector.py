import os

from ultralytics import YOLO


class HelmetDetector:

    def __init__(self, model_path, confidence=0.35):

        self.model_path = model_path
        self.confidence = confidence

        self.available = False
        self.model = None
        self.class_names = {}

        if not os.path.exists(model_path):

            print(
                f"[HELMET] Model not found: {model_path}"
            )

            print(
                "[HELMET] Helmet detection disabled."
            )

            return

        try:

            self.model = YOLO(model_path)

            self.class_names = self.model.names

            self.available = True

            print(
                f"[HELMET] Model loaded: {model_path}"
            )

            print(
                f"[HELMET] Classes: {self.class_names}"
            )

        except Exception as error:

            print(
                f"[HELMET] Model loading failed: {error}"
            )

            self.available = False

    def detect(self, frame):

        if not self.available:

            return []

        try:

            results = self.model.predict(
                source=frame,
                conf=self.confidence,
                verbose=False
            )

        except Exception as error:

            print(
                f"[HELMET] Detection error: {error}"
            )

            return []

        if not results:

            return []

        result = results[0]

        if result.boxes is None:

            return []

        detections = []

        for box in result.boxes:

            xyxy = box.xyxy[0].tolist()

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            class_name = self.class_names.get(
                class_id,
                str(class_id)
            )

            detections.append(
                {
                    "bbox": [
                        int(xyxy[0]),
                        int(xyxy[1]),
                        int(xyxy[2]),
                        int(xyxy[3])
                    ],

                    "class_id": class_id,

                    "class_name": str(
                        class_name
                    ).lower(),

                    "confidence": confidence
                }
            )

        return detections