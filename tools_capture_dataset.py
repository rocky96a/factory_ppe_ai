import cv2
import os
import time
import sys

BASE_DIR = "datasets/factory_raw"

FOLDERS = {
    "1": "no_helmet",
    "2": "helmet",
    "3": "mixed",
}

for folder in FOLDERS.values():
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)


def count_images(folder):
    path = os.path.join(BASE_DIR, folder)

    return len([
        f for f in os.listdir(path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])


print()
print("========================================")
print(" FACTORY PPE DATASET CAPTURE")
print("========================================")
print()
print("1 = NO HELMET")
print("2 = HELMET")
print("3 = MIXED")
print("Q = QUIT")
print()

choice = input("Select category: ").strip().lower()

if choice == "q":
    sys.exit(0)

if choice not in FOLDERS:
    print("Invalid selection.")
    sys.exit(1)

folder = FOLDERS[choice]

try:
    number = int(input("How many images to capture? ").strip())
except ValueError:
    print("Invalid number.")
    sys.exit(1)

try:
    interval = float(input("Seconds between images [2]: ").strip() or "2")
except ValueError:
    interval = 2.0

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print()
    print("ERROR: Webcam could not be opened.")
    print("Check that /dev/video0 is available.")
    sys.exit(1)

print()
print("========================================")
print(f" CATEGORY : {folder}")
print(f" IMAGES   : {number}")
print(f" INTERVAL : {interval} seconds")
print("========================================")
print()
print("Position yourself in front of the camera.")
print("Capture will begin in 5 seconds.")
print()

for remaining in range(5, 0, -1):
    print(f"Starting in {remaining}...")
    time.sleep(1)

saved = 0
counter = count_images(folder) + 1

while saved < number:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read webcam frame.")
        break

    filename = (
        f"{folder}_{counter:05d}_"
        f"{int(time.time())}.jpg"
    )

    path = os.path.join(BASE_DIR, folder, filename)

    success = cv2.imwrite(path, frame)

    if success:
        saved += 1
        counter += 1

        print(
            f"[{saved}/{number}] SAVED: {path}"
        )
    else:
        print("ERROR: Could not save image.")

    if saved < number:
        time.sleep(interval)

cap.release()

print()
print("========================================")
print(" CAPTURE COMPLETE")
print("========================================")
print(f"Category : {folder}")
print(f"Saved    : {saved}")
print()

for key, name in FOLDERS.items():
    print(
        f"{name:12s}: "
        f"{count_images(name)} images"
    )

print()