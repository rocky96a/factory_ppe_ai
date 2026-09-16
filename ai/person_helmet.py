"""
Person <-> Helmet association.

Rules:
1. Only objects already identified as PERSON can receive helmet status.
2. A helmet/no-helmet detection must be associated with the
   corresponding person's upper/head region.
3. One helmet detection can belong to only one person.
4. A helmet from another nearby person must not be reused.
5. Unknown is preferred over making a dangerous false violation.
"""

import math


# ============================================================
# CLASS HELPERS
# ============================================================

def _normalise_name(name):
    if name is None:
        return ""

    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def helmet_is_positive(class_name):
    name = _normalise_name(class_name)

    positive_names = {
        "helmet",
        "safety_helmet",
        "with_helmet",
        "hardhat",
        "hard_hat",
    }

    if name in positive_names:
        return True

    return (
        "helmet" in name
        and "no_helmet" not in name
        and "nohelmet" not in name
        and "without" not in name
        and "missing" not in name
    )


def helmet_is_negative(class_name):
    name = _normalise_name(class_name)

    negative_names = {
        "no_helmet",
        "nohelmet",
        "without_helmet",
        "missing_helmet",
        "helmet_missing",
        "no_hardhat",
        "no_hard_hat",
    }

    if name in negative_names:
        return True

    return (
        "no_helmet" in name
        or "nohelmet" in name
        or "without_helmet" in name
        or "missing_helmet" in name
    )


# ============================================================
# GEOMETRY
# ============================================================

def _center(box):
    x1, y1, x2, y2 = box

    return (
        (x1 + x2) / 2.0,
        (y1 + y2) / 2.0
    )


def _box_area(box):
    x1, y1, x2, y2 = box

    return max(0.0, x2 - x1) * max(
        0.0,
        y2 - y1
    )


def _point_inside_box(point, box):
    px, py = point
    x1, y1, x2, y2 = box

    return (
        x1 <= px <= x2
        and
        y1 <= py <= y2
    )


def _distance(p1, p2):
    return math.sqrt(
        (p1[0] - p2[0]) ** 2
        +
        (p1[1] - p2[1]) ** 2
    )


# ============================================================
# PERSON HEAD REGION
# ============================================================

def _head_region(person_box):
    """
    Return the upper/head region of a person.

    We intentionally do NOT use the entire person box.

    This prevents a helmet belonging to a nearby person from
    being associated with somebody else's body.
    """

    x1, y1, x2, y2 = person_box

    width = max(1.0, x2 - x1)
    height = max(1.0, y2 - y1)

    # Upper 35% of person.
    hx1 = x1
    hx2 = x2

    hy1 = y1
    hy2 = y1 + height * 0.35

    # Slight horizontal tightening.
    margin = width * 0.10

    hx1 += margin
    hx2 -= margin

    return (
        hx1,
        hy1,
        hx2,
        hy2
    )


# ============================================================
# HELMET MATCH SCORE
# ============================================================

def _match_score(person_box, helmet_box):
    """
    Lower score = better match.

    A helmet should:
    - be inside / near the person's head region
    - be near the top of the person
    """

    head = _head_region(person_box)

    helmet_center = _center(helmet_box)
    person_center = _center(person_box)

    # --------------------------------------------------------
    # Strong requirement: helmet center should be in or very
    # close to the head region.
    # --------------------------------------------------------

    hx1, hy1, hx2, hy2 = head

    px, py = helmet_center

    head_width = max(1.0, hx2 - hx1)
    head_height = max(1.0, hy2 - hy1)

    # Expanded head region for small camera/model errors.
    expanded_head = (
        hx1 - head_width * 0.35,
        hy1 - head_height * 0.60,
        hx2 + head_width * 0.35,
        hy2 + head_height * 0.60
    )

    if not _point_inside_box(
        helmet_center,
        expanded_head
    ):
        return None

    # --------------------------------------------------------
    # Distance from person center.
    # --------------------------------------------------------

    distance = _distance(
        helmet_center,
        person_center
    )

    person_height = max(
        1.0,
        person_box[3] - person_box[1]
    )

    normalised_distance = (
        distance / person_height
    )

    # --------------------------------------------------------
    # Vertical position.
    # --------------------------------------------------------

    vertical_offset = max(
        0.0,
        py - person_box[1]
    ) / person_height

    # Smaller is better.
    return (
        normalised_distance
        +
        vertical_offset * 0.75
    )


# ============================================================
# MAIN ASSOCIATION
# ============================================================

def associate_helmets(
    persons,
    helmet_detections,
    model_available=True
):
    """
    Associate helmet detections with multiple tracked people.

    Example:

        Person ID 1 -> HELMET
        Person ID 2 -> NO_HELMET
        Person ID 3 -> HELMET
        ...
        Person ID 20 -> UNKNOWN

    There is no hard-coded person limit.
    """

    if persons is None:
        persons = []

    if helmet_detections is None:
        helmet_detections = []

    results = []

    # --------------------------------------------------------
    # MODEL UNAVAILABLE
    # --------------------------------------------------------

    if not model_available:

        for person in persons:

            result = dict(person)

            result["helmet"] = None
            result["helmet_status"] = "UNKNOWN"
            result["helmet_confidence"] = 0.0
            result["helmet_bbox"] = None

            results.append(result)

        return results

    # --------------------------------------------------------
    # Prepare helmet detections
    # --------------------------------------------------------

    valid_helmets = []

    for index, helmet in enumerate(
        helmet_detections
    ):

        if not isinstance(helmet, dict):
            continue

        bbox = helmet.get("bbox")

        if not bbox or len(bbox) != 4:
            continue

        class_name = helmet.get(
            "class_name",
            helmet.get("class", "")
        )

        confidence = float(
            helmet.get(
                "confidence",
                0.0
            ) or 0.0
        )

        if not (
            helmet_is_positive(class_name)
            or
            helmet_is_negative(class_name)
        ):
            continue

        valid_helmets.append(
            {
                "index": index,
                "bbox": bbox,
                "class_name": class_name,
                "confidence": confidence,
            }
        )

    # --------------------------------------------------------
    # Build candidate matches.
    #
    # Each candidate:
    # (score, person_index, helmet_index)
    # --------------------------------------------------------

    candidates = []

    for person_index, person in enumerate(persons):

        person_box = person.get("bbox")

        if not person_box:
            continue

        for helmet_index, helmet in enumerate(
            valid_helmets
        ):

            score = _match_score(
                person_box,
                helmet["bbox"]
            )

            if score is None:
                continue

            candidates.append(
                (
                    score,
                    person_index,
                    helmet_index
                )
            )

    # --------------------------------------------------------
    # GLOBAL ONE-TO-ONE MATCHING
    #
    # This is important for crowded scenes.
    #
    # One helmet detection cannot be assigned to
    # two different people.
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: item[0]
    )

    assigned_people = set()
    assigned_helmets = set()

    matches = {}

    for (
        score,
        person_index,
        helmet_index
    ) in candidates:

        if person_index in assigned_people:
            continue

        if helmet_index in assigned_helmets:
            continue

        assigned_people.add(person_index)
        assigned_helmets.add(helmet_index)

        matches[person_index] = (
            score,
            valid_helmets[helmet_index]
        )

    # --------------------------------------------------------
    # Apply results to EVERY person
    # --------------------------------------------------------

    for person_index, person in enumerate(persons):

        result = dict(person)

        # ----------------------------------------------------
        # No reliable helmet match
        # ----------------------------------------------------

        if person_index not in matches:

            result["helmet"] = None
            result["helmet_status"] = "UNKNOWN"
            result["helmet_confidence"] = 0.0
            result["helmet_bbox"] = None

            results.append(result)

            continue

        score, helmet = matches[
            person_index
        ]

        class_name = helmet[
            "class_name"
        ]

        confidence = helmet[
            "confidence"
        ]

        result["helmet_bbox"] = helmet[
            "bbox"
        ]

        result["helmet_class"] = class_name

        # ----------------------------------------------------
        # HELMET
        # ----------------------------------------------------

        if helmet_is_positive(
            class_name
        ):

            result["helmet"] = True

            result[
                "helmet_status"
            ] = "HELMET"

            result[
                "helmet_confidence"
            ] = confidence

        # ----------------------------------------------------
        # NO HELMET
        # ----------------------------------------------------

        elif helmet_is_negative(
            class_name
        ):

            result["helmet"] = False

            result[
                "helmet_status"
            ] = "NO_HELMET"

            result[
                "helmet_confidence"
            ] = confidence

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        else:

            result["helmet"] = None

            result[
                "helmet_status"
            ] = "UNKNOWN"

            result[
                "helmet_confidence"
            ] = 0.0

        results.append(result)

    return results
