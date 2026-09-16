import cv2
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("CAMERA_01_RTSP")

if not url:
    raise RuntimeError(
        "CAMERA_01_RTSP is not configured in .env"
    )

print("Connecting to RTSP camera...")
print(url)

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("ERROR: Could not open RTSP stream.")
    raise SystemExit(1)

print("RTSP connection successful.")

while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read frame.")
        break

    cv2.imshow(
        "CAM-01 LIVE",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()