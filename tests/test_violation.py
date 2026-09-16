from ai.violation_engine import (
    ViolationEngine
)


def test_violation_engine():

    engine = ViolationEngine(
        confirmation_frames=2,
        cooldown_seconds=30
    )

    persons = [
        {
            "track_id": 1,
            "bbox": [10, 10, 100, 200],
            "confidence": 0.9,
            "helmet": False
        }
    ]

    result1 = engine.process(
        "CAM-01",
        persons
    )

    assert result1 == []

    result2 = engine.process(
        "CAM-01",
        persons
    )

    assert len(result2) == 1

    assert (
        result2[0]["detection"]
        == "NO_HELMET"
    )