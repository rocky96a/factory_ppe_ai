from pathlib import Path
import cv2
import time
import random

BASE = Path("/home/souvik/bakup/factory_ppe_ai")
OUT = BASE / "datasets/factory_raw/no_helmet_diverse"
OUT.mkdir(parents=True, exist_ok=True)

TOTAL = 300

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened.")
    raise SystemExit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print()
print("=" * 60)
print("AUTOMATIC NO-HELMET DATASET CAPTURE")
print("=" * 60)
print()
print("300 images will be captured automatically.")
print()
print("Change your position naturally during capture.")
print("Try front, left, right, close, far, looking up/down, etc.")
print()
print("NO annotation is required.")
print()
print("Starting in 5 seconds...")
time.sleep(5)

saved = 0

while saved < TOTAL:

    ret, frame = cap.read()

    if not ret:
        print("Camera frame failed.")
        time.sleep(1)
        continue

    filename = OUT / f"no_helmet_{saved + 1:04d}.jpg"
    cv2.imwrite(str(filename), frame)

    saved += 1

    if saved % 10 == 0:
        print(f"Captured {saved}/{TOTAL}")

    if saved % 30 == 0 and saved < TOTAL:
        suggestions = [
            "Move to the LEFT side.",
            "Move to the RIGHT side.",
            "Move CLOSER.",
            "Move FARTHER away.",
            "Turn your face LEFT and RIGHT.",
            "Look UP and DOWN.",
            "Stand at a different angle.",
            "Walk slowly across the camera.",
            "Change your position.",
            "Move naturally."
        ]

        print()
        print(">>> CHANGE POSITION:")
        print(">>> " + random.choice(suggestions))
        print()

        time.sleep(4)

    time.sleep(random.uniform(1.5, 2.5))

cap.release()

print()
print("=" * 60)
print("CAPTURE COMPLETE")
print("=" * 60)
print(f"Images captured: {saved}")
print(f"Saved to: {OUT}")
