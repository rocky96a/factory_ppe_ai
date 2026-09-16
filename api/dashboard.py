from flask import Blueprint, jsonify

from database.db import (
    get_violations,
    get_cameras
)


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.get("")
def dashboard():

    violations = get_violations(
        limit=1000
    )

    cameras = get_cameras()

    today_violations = len(
        violations
    )

    return jsonify({
        "success": True,
        "camera_count": len(cameras),
        "violation_count": today_violations,
        "recent_violations": violations[:10]
    })