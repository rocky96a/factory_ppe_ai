from flask import Blueprint, jsonify

from database.db import get_violations, get_violation


violations_bp = Blueprint(
    "violations",
    __name__,
    url_prefix="/api"
)


@violations_bp.route("/violations", methods=["GET"])
def violations():

    try:
        rows = get_violations(limit=100)

        return jsonify({
            "success": True,
            "violations": rows,
            "count": len(rows)
        })

    except Exception as exc:

        print(
            f"[API ERROR] /api/violations: {exc}"
        )

        return jsonify({
            "success": False,
            "error": str(exc),
            "violations": []
        }), 500


@violations_bp.route(
    "/violations/<int:violation_id>",
    methods=["GET"]
)
def violation_detail(violation_id):

    try:
        violation = get_violation(
            violation_id
        )

        if violation is None:

            return jsonify({
                "success": False,
                "error": "Violation not found"
            }), 404

        return jsonify({
            "success": True,
            "violation": violation
        })

    except Exception as exc:

        print(
            f"[API ERROR] "
            f"/api/violations/{violation_id}: {exc}"
        )

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500