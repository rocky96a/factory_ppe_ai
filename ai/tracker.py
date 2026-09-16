from ultralytics import YOLO


class PersonTracker:
    """
    Person-only detector + tracker.

    IMPORTANT:
    COCO class 0 = person.

    This means hands, helmets, boxes, machines, chairs, tools,
    etc. are NOT passed into the tracking system as people.
    """

    PERSON_CLASS_ID = 0

    def __init__(self, model_path, confidence=0.35):
        self.model_path = model_path
        self.confidence = confidence

        self.model = YOLO(model_path)

        print(
            f"[TRACKER] Model loaded: {model_path}"
        )

        print(
            f"[TRACKER] PERSON ONLY | "
            f"class={self.PERSON_CLASS_ID} | "
            f"confidence={self.confidence}"
        )

    def track(self, frame):
        """
        Detect and track ALL visible people.

        There is intentionally no maximum of 2 or 3 people.
        Ultralytics returns as many person detections as are
        available in the frame.
        """

        results = self.model.track(
            frame,
            persist=True,
            classes=[self.PERSON_CLASS_ID],
            conf=self.confidence,
            verbose=False
        )

        persons = []

        if not results:
            return persons

        result = results[0]

        if result.boxes is None:
            return persons

        boxes = result.boxes

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()

        if boxes.id is not None:
            track_ids = (
                boxes.id
                .cpu()
                .numpy()
                .astype(int)
            )
        else:
            track_ids = [
                None
            ] * len(xyxy)

        for bbox, confidence, track_id in zip(
            xyxy,
            confs,
            track_ids
        ):
            x1, y1, x2, y2 = bbox.astype(int)

            persons.append(
                {
                    "track_id": (
                        int(track_id)
                        if track_id is not None
                        else None
                    ),
                    "bbox": (
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ),
                    "person_confidence": float(
                        confidence
                    ),
                    "class_id": self.PERSON_CLASS_ID,
                    "class_name": "person"
                }
            )

        return persons
