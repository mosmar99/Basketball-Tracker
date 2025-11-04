# Simple inference pipeline for ruinning models from roboflow locally
# requires
# pip install inference
# OR
# pip install inference-gpu

# Import the InferencePipeline object
from inference import InferencePipeline
# Import the built in render_boxes sink for visualizing results
from inference.core.interfaces.stream.sinks import VideoFileSink
import os

output_dir = "results"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "video_1_predictions.avi")

video_sink = VideoFileSink.init(video_file_name=output_path)

# initialize a pipeline object
pipeline = InferencePipeline.init(
    model_id="basketball-1zhpe/1", # Roboflow model to use
    video_reference="./input_videos/video_1.mp4", # Path to video, device id (int, usually 0 for built in webcams), or RTSP stream url
    on_prediction=video_sink.on_prediction,
    api_key="EFXJ05KcCz7Z9pLWavlS"
)
pipeline.start()
pipeline.join()

video_sink.release()