import gradio as gr
import requests
import json
import cv2
import os
import numpy as np
import ui_service.config as config
from shared.storage import upload_video, download_to_temp

def sort_points(points):
    pts = np.array(points, dtype="float32")
    
    xSorted = pts[np.argsort(pts[:, 0]), :]

    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]

    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost

    rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
    (tr, br) = rightMost

    return [tl.tolist(), tr.tolist(), br.tolist(), bl.tolist()]

def stitch(video_path):
    if not video_path: return None, None, "No video!", None
    try:
        basename = os.path.basename(video_path)
        upload_video(video_path, basename, config.BUCKET_RAW)
        
        with open(video_path, "rb") as f:
            resp = requests.post(config.API_STITCH, files={"video": (basename, f, "video/mp4")})
        
        if resp.status_code != 200:
            return None, None, f"Stitch Error: {resp.text}", None
            
        data = resp.json()
        panorama_uri = data["panorama_uri"]
        
        bucket, key = panorama_uri.replace("s3://", "").split("/", 1)
        local_pano = download_to_temp(key, bucket)
        
        return local_pano, [], panorama_uri, "Stitched! Click the 4 court corners in the stitched image.", local_pano
    except Exception as e:
        return None, None, None, str(e), None

def draw_points(image, points):
    image = cv2.imread(image)
    if image is not None:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
    if image is None:
        return None

    if len(points) > 1:
        is_closed = (len(points) == 4)
        
        pts_np = np.array(points, np.int32)
        pts_np = pts_np.reshape((-1, 1, 2))
        
        cv2.polylines(image, [pts_np], is_closed, (255, 0, 0), 2)

    for i, pt in enumerate(points):
        x, y = int(pt[0]), int(pt[1])
        
        cv2.circle(image, (x, y), 10, (255, 0, 0), -1) 
        
        label = str(i + 1)
        cv2.putText(image, label, (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
    return image

def add_point(original_img, points, evt: gr.SelectData):
    if original_img is None: 
        return None, points
    if len(points) >= 4: 
        return draw_points(original_img, points), points 
    
    x, y = evt.index
    points.append([x, y])
    
    if len(points) == 4:
        points = sort_points(points)

    final_img = draw_points(original_img, points)
    
    return final_img, points

def warp(panorama_uri, points, court_name):
    if len(points) != 4: 
        return "Error: You must select exactly 4 points."
    if not court_name or not court_name.strip(): 
        return "Error: Please enter a name."
        
    try:
        payload = {
            "panorama_uri": panorama_uri,
            "points_json_str": json.dumps(points),
            "court_name": court_name.strip()
        }
        resp = requests.post(config.API_WARP, data=payload)
        
        return f"Success! Court '{court_name}' created." if resp.status_code == 200 else f"Warp Error: {resp.text}"
    except Exception as e:
        return f"Error: {e}"

def render_court_tab():
    with gr.TabItem("Create Reference Court"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Panorama Stitch Input")
                stitch_video_in = gr.Video(label="Upload Reference Video", include_audio=False)
                stitch_btn = gr.Button("Stitch Panorama", variant="primary")
                stitch_status = gr.Textbox(label="Status", interactive=False)
                
                panorama_uri_state = gr.State()
                points_state = gr.State([])
                original_pano_state = gr.State()

            with gr.Column(scale=2):
                gr.Markdown("### Annotate Stitched Panorama")
                annotation_img = gr.Image(label="Click the 4 Court Corners", interactive=True)
                
                with gr.Row():
                    court_name_in = gr.Textbox(label="Court Name", placeholder="Lakers", scale=2)
                    reset_btn = gr.Button("Reset Points", scale=1)
                    warp_btn = gr.Button("Save Court", variant="stop", scale=1)
        
        stitch_btn.click(
            stitch, 
            inputs=[stitch_video_in], 
            outputs=[annotation_img, points_state, panorama_uri_state, stitch_status, original_pano_state]
        )
        
        annotation_img.select(
            add_point, 
            inputs=[original_pano_state, points_state], 
            outputs=[annotation_img, points_state]
        )
        
        reset_btn.click(
            lambda x: (x, []), 
            inputs=[original_pano_state], 
            outputs=[annotation_img, points_state]
        )
        
        warp_btn.click(
            warp, 
            inputs=[panorama_uri_state, points_state, court_name_in], 
            outputs=[stitch_status]
        )