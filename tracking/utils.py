import os
import wandb
from pathlib import Path

import sys
sys.path.append("../")
from dotenv import load_dotenv
load_dotenv()

def get_production_model_path():
    load_dotenv()
    key = os.getenv("WNB_API_TOKEN")
    if key is None:
        raise EnvironmentError("Environment variable WNB_API_TOKEN is not set")

    wandb.login(key=key)

    artifact_ref = (
        "mosmar99-j-nk-ping-university-org/"
        "wandb-registry-model/general-object-detection:production"
    )

    api = wandb.Api()
    artifact = api.artifact(artifact_ref, type="model")

  # 3) Resolve <project_root>/models/prod
    project_root = Path(__file__).resolve().parent.parent
    models_root = project_root / "models"
    prod_dir = models_root / "prod"
    prod_dir.mkdir(parents=True, exist_ok=True)

    # 4) Clear old prod weights
    for p in prod_dir.glob("*.pt"):
        p.unlink()

    # 5) Download artifact directly into prod_dir
    download_dir = Path(artifact.download(root=str(prod_dir)))

    # Depending on W&B, download_dir may be prod_dir itself or a subfolder;
    # just search inside prod_dir for a .pt file.
    try:
        weights_path = next(prod_dir.rglob("*.pt"))
    except StopIteration:
        raise FileNotFoundError(
            f"No .pt weights found in downloaded artifact under {prod_dir}"
        )

    print(f"[W&B] Production model stored at {weights_path}, size={weights_path.stat().st_size} bytes")

    return weights_path

# weights_path = get_production_model_path()
# print(weights_path)