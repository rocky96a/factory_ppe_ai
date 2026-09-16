from pathlib import Path
import cv2
import time
import random

OUT = Path("/home/souvik/bakup/factory_ppe_ai/datasets/factory_raw/no_helmet")
TARGET = 300

OUT.mkdir(parents=True, exist_ok=True)

files = [
    p for p in OUT.iterdir()
    if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
]

existing = len(files)
remaining = TARGET - existing

print("=" * 50)
print("NO-HELMET DATASET")
print("=" * 50)
print(f"Existing : {existing}")
print(f"Target   : {TARGET}")
print(f"To add   : {max(0, remaining)}")
print("=" * 50)

if remaining <= 0:
    print("Already have 300 images. Nothing to capture.")
    raise SystemExit

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened.")
    raise SystemExit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print()
print("Starting in 5 seconds...")
print("Change your position naturally.")
print()

time.sleep(5)

suggestions = [
    "Move LEFT",
    "Move RIGHT",
    "Move CLOSER",
    "Move FARTHER",
    "Turn face LEFT",
    "Turn face RIGHT",
    "Look UP / DOWN",
    "Walk across camera",
    "Change angle",
    "Change position"
]

saved = 0

while saved < remaining:

    ret, frame = cap.read()

    if not ret:
        print("Camera read failed.")
        time.sleep(1)
        continue

    number = existing + saved + 1
    filename = OUT / f"no_helmet_{number:05d}_{int(time.time())}.jpg"

    ok = cv2.imwrite(str(filename), frame)

    if ok:
        saved += 1
        print(f"Captured {saved}/{remaining}: {filename.name}")

    if saved % 25 == 0 and saved < remaining:
        print()
        print(">>> CHANGE POSITION:", random.choice(suggestions))
        print()
        time.sleep(4)

    time.sleep(random.uniform(1.5, 2.5))

cap.release()

print()
print("=" * 50)
print("CAPTURE COMPLETE")
print("=" * 50)
print(f"Existing before : {existing}")
print(f"New captured    : {saved}")
print(f"Total now       : {existing + saved}")
print("=" * 50)
