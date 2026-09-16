from flask import Blueprint, jsonify

from database.db import get_cameras


cameras_bp = Blueprint(
    "cameras",
    __name__,
    url_prefix="/api/cameras"
)


@cameras_bp.get("")
def cameras():

    return jsonify({
        "success": True,
        "cameras": get_cameras()
    })