from ultralytics import YOLO


class PersonDetector:

    def __init__(
        self,
        model_path,
        confidence=0.35
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            classes=[0],
            verbose=False
        )

        if not results:
            return []

        result = results[0]

        detections = []

        if result.boxes is None:
            return detections

        for box in result.boxes:

            xyxy = box.xyxy[0].tolist()

            confidence = float(
                box.conf[0]
            )

            detections.append({
                "bbox": [
                    int(xyxy[0]),
                    int(xyxy[1]),
                    int(xyxy[2]),
                    int(xyxy[3])
                ],
                "confidence": confidence,
                "class_id": 0,
                "class_name": "person"
            })

        return detections