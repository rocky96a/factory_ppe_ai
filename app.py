import os
import cv2

from flask import (
    Flask,
    render_template,
    Response,
    jsonify,
    send_from_directory
)

from flask_cors import CORS

from config import Config

from database.db import (
    init_db,
    get_cameras,
    add_camera
)

from cameras.camera_manager import (
    CameraManager
)

from api.cameras import cameras_bp
from api.violations import violations_bp
from api.dashboard import dashboard_bp
from api.browser_camera import browser_camera_bp


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

CORS(app)

app.config.from_object(Config)


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs(Config.EVIDENCE_DIR, exist_ok=True)
os.makedirs(Config.SNAPSHOT_DIR, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# CAMERA MANAGER
# ============================================================

camera_manager = CameraManager()


def load_cameras():
    """
    Load all enabled cameras from SQLite
    and add them to CameraManager.
    """

    cameras = get_cameras()

    for camera in cameras:

        if not camera["enabled"]:
            continue

        camera_manager.add_camera(
            camera_id=camera["camera_id"],
            name=camera["name"],
            location=camera["location"],
            stream_url=camera["stream_url"]
        )


# ============================================================
# MAIN DASHBOARD
# ============================================================

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ============================================================
# CAMERAS PAGE
# ============================================================

@app.route("/cameras")
def cameras_page():
    return render_template("cameras.html")


# ============================================================
# VIOLATIONS PAGE
# ============================================================

@app.route("/violations")
def violations_page():
    return render_template("violations.html")


# ============================================================
# LIVE CAMERA VIDEO
# ============================================================

@app.route("/video/<camera_id>")
def video(camera_id):

    def generate():

        while True:

            frame = camera_manager.get_frame(
                camera_id
            )

            if frame is None:
                continue

            success, encoded = cv2.imencode(
                ".jpg",
                frame
            )

            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + encoded.tobytes()
                + b"\r\n"
            )

    return Response(
        generate(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


# ============================================================
# EVIDENCE IMAGE
# ============================================================

@app.route("/evidence/<path:filename>")
def evidence(filename):

    return send_from_directory(
        Config.EVIDENCE_DIR,
        filename
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return jsonify({
        "success": True,
        "service": "Factory PPE AI",
        "status": "running"
    })


# ============================================================
# API BLUEPRINTS
# ============================================================

app.register_blueprint(cameras_bp)

app.register_blueprint(violations_bp)

app.register_blueprint(dashboard_bp)
app.register_blueprint(browser_camera_bp)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    load_cameras()

    print("")
    print("=" * 60)
    print("FACTORY PPE AI")
    print("=" * 60)

    print(
        f"Dashboard: "
        f"http://127.0.0.1:{Config.APP_PORT}"
    )

    print(
        f"Violations: "
        f"http://127.0.0.1:{Config.APP_PORT}/violations"
    )

    print(
        f"API: "
        f"http://127.0.0.1:{Config.APP_PORT}/api/violations"
    )

    print("=" * 60)

    app.run(
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        debug=Config.DEBUG,
        threaded=True,
        use_reloader=False
    )