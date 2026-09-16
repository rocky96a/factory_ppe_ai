from pathlib import Path
from huggingface_hub import hf_hub_download

REPO = "rocky0912www/factory-ppe-models"

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
MODELS.mkdir(parents=True, exist_ok=True)

print("[MODEL] Downloading yolo11n.pt...")

hf_hub_download(
    repo_id=REPO,
    filename="yolo11n.pt",
    local_dir=str(ROOT),
)

print("[MODEL] Downloading helmet.pt...")

hf_hub_download(
    repo_id=REPO,
    filename="helmet.pt",
    local_dir=str(MODELS),
)

print("[MODEL] All models ready.")
