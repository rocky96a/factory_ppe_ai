import time


class ViolationEngine:

    def __init__(
        self,
        confirmation_frames=5,
        cooldown_seconds=30
    ):

        self.confirmation_frames = (
            confirmation_frames
        )

        self.cooldown_seconds = (
            cooldown_seconds
        )

        self.no_helmet_frames = {}

        self.last_violation = {}

    def process(
        self,
        camera_id,
        persons
    ):

        violations = []

        now = time.time()

        for person in persons:

            track_id = person.get(
                "track_id"
            )

            if track_id is None:

                continue

            key = (
                camera_id,
                track_id
            )

            helmet = person.get(
                "helmet"
            )

            # -------------------------------------------------
            # HELMET
            # -------------------------------------------------

            if helmet is True:

                self.no_helmet_frames[key] = 0

                continue

            # -------------------------------------------------
            # UNKNOWN
            # -------------------------------------------------

            if helmet is None:

                # Do NOT count unknown as violation.
                continue

            # -------------------------------------------------
            # NO HELMET
            # -------------------------------------------------

            self.no_helmet_frames[key] = (
                self.no_helmet_frames.get(
                    key,
                    0
                )
                + 1
            )

            frame_count = (
                self.no_helmet_frames[key]
            )

            last_time = (
                self.last_violation.get(
                    key,
                    0
                )
            )

            cooldown_finished = (
                now - last_time
                >= self.cooldown_seconds
            )

            # -------------------------------------------------
            # CONFIRMED VIOLATION
            # -------------------------------------------------

            if (
                frame_count
                >= self.confirmation_frames
                and
                cooldown_finished
            ):

                self.last_violation[key] = now

                violations.append(
                    {
                        "track_id": track_id,

                        "confidence": person.get(
                            "helmet_confidence",
                            person.get(
                                "confidence",
                                0.0
                            )
                        ),

                        "detection": "NO_HELMET"
                    }
                )

        return violations