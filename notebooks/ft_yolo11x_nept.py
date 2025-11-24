import os
import neptune
from pathlib import Path
from roboflow import Roboflow
from ultralytics import YOLO
from dotenv import load_dotenv


def init_neptune_run(hyperparameters):
    """Initialize a Neptune run and log metadata."""
    run = neptune.init_run(
        project="mosmar99/general",
        api_token=os.getenv("NEPTUNE_API_TOKEN"),
    )

    # Add metadata
    run["sys/group_tags"].add(["basketball-tracker"])
    run["sys/tags"].add(["yolov11x", "finetune", f"epochs={hyperparameters['epochs']}"])
    run["project/name"] = "basketball_tracking"
    run["model/basedmodel_name"] = "yolov11x"
    run["model/task"] = "object_detection"
    run["model_configs/optimizer"] = "Adam"
    run["model_configs/lr0"] = hyperparameters["lr0"]
    run["model_configs/lrf"] = hyperparameters["lrf"]
    run["model_configs/epochs"] = hyperparameters["epochs"]

    return run


def download_dataset():
    """Download dataset from Roboflow and return path to data.yaml."""
    rf = Roboflow(api_key=os.getenv("ROBOFLOW_API_KEY"))
    project = rf.workspace("workspace-5ujvu").project("basketball-players-fy4c2-vfsuv")
    version = project.version(17)
    dataset = version.download("yolov11")
    return dataset.location + "/data.yaml"


def train_model(dataset_path, hyperparameters):
    """Fine-tune YOLO model on dataset."""
    os.environ["NEPTUNE_MODE"] = "offline"
    model = YOLO("models/yolo11x.pt")

    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    train_results = model.train(
        data=dataset_path,
        epochs=hyperparameters["epochs"],
        imgsz=640,
        device=0,
        plots=True,
        workers=0,
        batch=9,
        project=output_dir,
        lr0=hyperparameters["lr0"],
        lrf=hyperparameters["lrf"],
        name="finetuned",
    )
    return train_results


def log_metrics(run, train_results):
    """Log key training metrics to Neptune."""
    metrics = train_results.results_dict
    run["test_results/val/mAP50"] = metrics.get("metrics/mAP50(B)", 0)
    run["test_results/val/mAP50_95"] = metrics.get("metrics/mAP50-95(B)", 0)
    run["test_results/val/precision"] = metrics.get("metrics/precision(B)", 0)
    run["test_results/val/recall"] = metrics.get("metrics/recall(B)", 0)


def upload_training_artifacts(run, train_results):
    """Upload non-weight artifacts and best model to Neptune."""
    results_dir = Path(train_results.save_dir)
    if results_dir.exists():
        for file_path in results_dir.rglob("*"):
            if "weights" in file_path.parts:
                continue
            if file_path.is_file():
                neptune_path = f"training_results/{file_path.relative_to(results_dir).as_posix()}"
                run[neptune_path].upload(str(file_path))

    best_model_path = results_dir / "weights" / "best.pt"
    if best_model_path.exists():
        print(f"Uploading best model: {best_model_path}")
        run["model_weights_pt/best_model"].upload(str(best_model_path))
    else:
        print(f"Best model file not found at {best_model_path}, skipping upload.")


def main():
    """Main training pipeline."""
    load_dotenv()

    hyperparameters = {
        "epochs": 200,
        "lr0": 0.05,
        "lrf": 0.001,
    }

    run = init_neptune_run(hyperparameters)

    print("> Downloading dataset...")
    dataset_path = download_dataset()

    print("> Fine-tuning YOLO model...")
    train_results = train_model(dataset_path, hyperparameters)

    print("> Logging metrics to Neptune...")
    log_metrics(run, train_results)

    print("> Uploading results and best model...")
    upload_training_artifacts(run, train_results)

    run.stop()
    print("> Training and logging complete")

if __name__ == "__main__":
    main()
