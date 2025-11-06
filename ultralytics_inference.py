from ultralytics import YOLO # type: ignore
 
# Load a pretrained YOLO11n model
model = YOLO("models/ft_best.pt")
 
dataset_path = "/home/maso/university/advanced_ai_systems_vt2025p2/Basketball-Tracker/Basketball-Players-17/data.yaml"

# # Test (validate) the model on the dataset
# test_results = model.val(
#     data=dataset_path,  # Path to dataset configuration file
#     imgsz=640,          # Image size for testing
#     device=0,           # Device to run on
#     batch=8,            # Batch size
#     plots=True          # Save and display result plots
# )

# # Predict
# predict_results = model.predict("input_videos/video_1.mp4", save=True)

# Predict
predict_results = model.track("input_videos/video_1.mp4", save=True)

