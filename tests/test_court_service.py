# test_script.py (CORRECTED)
import requests
import os

def build_panorama_service(local_video_path: str):
    # Ensure the files exist before trying to open them
    if not os.path.exists(local_video_path):
        raise FileNotFoundError(f"Video file not found: {local_video_path}")

    url = "http://localhost:8002/stitch"
    
    # Open both files with their own handles
    with open(local_video_path, "rb") as video_file:
        
        # Use the correct file handles for each part
        files = {
            "video": ("video.mp4", video_file, "video/mp4"),
        }
        
        print("Sending request to server...")
        r = requests.post(url, files=files)
    
    r.raise_for_status()
    data = r.json()
    
    # Your server will return a key 'homographies' in the corrected code below
    return data

def get_homographies_from_service(local_video_path: str, local_reference_path: str):
    # Ensure the files exist before trying to open them
    if not os.path.exists(local_video_path):
        raise FileNotFoundError(f"Video file not found: {local_video_path}")
    if not os.path.exists(local_reference_path):
        raise FileNotFoundError(f"Reference image not found: {local_reference_path}")

    url = "http://localhost:8002/homographyvideo"
    
    # Open both files with their own handles
    with open(local_video_path, "rb") as video_file, \
         open(local_reference_path, "rb") as reference_file:
        
        # Use the correct file handles for each part
        files = {
            "video": ("video.mp4", video_file, "video/mp4"),
            "reference": ("reference.jpg", reference_file, "image/jpeg")
        }
        
        print("Sending request to server...")
        r = requests.post(url, files=files)
    
    r.raise_for_status()
    data = r.json()
    
    return data["H"]

if __name__ == '__main__':
    video_path = "../input_videos/video_1.mp4"
    ref_path = "../court_homography_exploration/imgs/full_court_warped.jpg"
    
    results = get_homographies_from_service(video_path, ref_path)
    
    print(f"Successfully received {len(results)} homography results.")
    # Print the first result as an example
    if results:
        print("First homography matrix:", results[0])

    results = build_panorama_service(video_path)
    print(results)