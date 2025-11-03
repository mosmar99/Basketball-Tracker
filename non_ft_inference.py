from ultralytics import YOLO # type: ignore

model = YOLO("./models/yolov11x.pt")

results = model.predict("input_videos/video_1.mp4", save=True)

print(results)
print("======================")

for box in results[0].boxes:
    print(box.xyxy)


