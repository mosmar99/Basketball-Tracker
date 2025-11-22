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
    api = wandb.Api()
    artifact = api.artifact(
        "mosmar99-j-nk-ping-university-org/wandb-registry-model/general-object-detection:production",
        type="model",
    )

    tmp_dir = Path(artifact.download(root="models"))
    weights_src = next(tmp_dir.glob("*.pt"))

    prod_dir = Path("models/prod")
    prod_dir.mkdir(parents=True, exist_ok=True)

    for p in prod_dir.glob("*.pt"):
        p.unlink()

    weights_dst = prod_dir / f"{artifact.name}.pt"
    weights_dst.write_bytes(weights_src.read_bytes())
    return weights_dst

# weights_path = get_production_model_path()
# print(weights_path)