import os
import cv2
import json
import requests
import gradio as gr
import ui_service.config as config
from shared.storage import upload_video, download_to_temp

def stitch(video_path):
    if not video_path: return None, None, "No video!"
    try:
        basename = os.path.basename(video_path)
        upload_video(video_path, basename, config.BUCKET_RAW)
        
        with open(video_path, "rb") as f:
            resp = requests.post(config.API_STITCH, files={"video": (basename, f, "video/mp4")})
        
        if resp.status_code != 200:
            return None, None, f"Stitch Error: {resp.text}"
            
        data = resp.json()
        panorama_uri = data["panorama_uri"]
        
        bucket, key = panorama_uri.replace("s3://", "").split("/", 1)
        local_pano = download_to_temp(key, bucket)
        
        return local_pano, [], panorama_uri, "Stitched! Click 4 corners on the image."
    except Exception as e:
        return None, None, None, str(e)

def add_point(img, evt: gr.SelectData, points):
    if len(points) >= 4: return img, points 
    x, y = evt.index
    points.append([x, y])
    img_draw = img.copy()
    
    if len(points) > 1:
        for i in range(len(points) - 1):
            cv2.line(img_draw, tuple(map(int, points[i])), tuple(map(int, points[i+1])), (255, 0, 0), 2)
    if len(points) == 4:
        cv2.line(img_draw, tuple(map(int, points[3])), tuple(map(int, points[0])), (255, 0, 0), 2)

    cv2.circle(img_draw, (x, y), 10, (255, 0, 0), -1) 
    cv2.putText(img_draw, str(len(points)), (x+15, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return img_draw, points

def warp(panorama_uri, points, court_name):
    if len(points) != 4: return "Error: You must select exactly 4 points."
    if not court_name or not court_name.strip(): return "Error: Please enter a name."
        
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
                
                # Hidden States
                panorama_uri_state = gr.State()
                points_state = gr.State([])
                original_pano_state = gr.State()

            with gr.Column(scale=2):
                gr.Markdown("### Annotate Stitched Panorama")
                annotation_img = gr.Image(label="Click 4 Corners", interactive=True)
                
                with gr.Row():
                    court_name_in = gr.Textbox(label="Court Name", placeholder="Lakers", scale=2)
                    reset_btn = gr.Button("Reset Points", scale=1)
                    warp_btn = gr.Button("Save Court", variant="stop", scale=1)
        
        stitch_btn.click(stitch, inputs=[stitch_video_in], outputs=[annotation_img, points_state, panorama_uri_state, stitch_status])
        annotation_img.change(lambda x: x, inputs=annotation_img, outputs=original_pano_state)
        annotation_img.select(add_point, inputs=[annotation_img, points_state], outputs=[annotation_img, points_state])
        reset_btn.click(lambda x: (x, []), inputs=[original_pano_state], outputs=[annotation_img, points_state])
        warp_btn.click(warp, inputs=[panorama_uri_state, points_state, court_name_in], outputs=[stitch_status])