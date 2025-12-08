import os
import cv2
import json
import requests
import numpy as np
import gradio as gr
from shared.storage import upload_video
import ui_service.config as config
from ui_service.plots import possession_plot, control_plot, pi_plots
from ui_service.utils import fetch_local_resource, list_courts

def to_desat_hex(bgr, factor=0.5):
    pixel = np.array([[bgr]], dtype=np.uint8)
    hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
    hsv[0, 0, 1] = np.clip(hsv[0, 0, 1] * factor, 0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    r, g, b = rgb[0, 0]
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def run_inference(video_file, court_name):
    if not video_file or not court_name:
        return [None]*5 + ["Missing inputs"]

    local_path = video_file
    basename = os.path.basename(local_path)
    video_name = basename.replace(".mp4", "")
    
    upload_video(local_path, basename, config.BUCKET_RAW)
    
    try:
        resp = requests.post(config.API_PROCESS, params={
            "video_name": video_name, 
            "reference_court": court_name
        })
    except:
        return [None]*5 + ["Backend unreachable"]

    if resp.status_code != 200:
        return [None]*5 + [f"Error: {resp.text}"]

    data = resp.json()
    vid_name = data["vid_name"]

    team_colors = json.loads(data["team_colors"])
    team_hex_colors = {
        k: to_desat_hex (v)
        for k, v in team_colors.items()
    }

    plot_poss = possession_plot(json.loads(data["ball_tp"]), team_hex_colors["1"], team_hex_colors["2"])
    plot_ctrl = control_plot(json.loads(data["control_stats"]), team_hex_colors["1"], team_hex_colors["2"])
    plot_pass, plot_intr = pi_plots(json.loads(data["pi_stats"]), team_hex_colors["1"], team_hex_colors["2"])
    
    url_proc = f"{config.VIEWER_BASE}/video/{config.BUCKET_PROCESSED}/{vid_name}"
    url_mini = f"{config.VIEWER_BASE}/video/{config.BUCKET_MINIMAP}/{vid_name}"
    
    return (
        fetch_local_resource(url_proc, ".mp4"),
        fetch_local_resource(url_mini, ".mp4"),
        plot_poss, 
        plot_ctrl,
        plot_pass,
        plot_intr,
        "Processing Complete!"
    )

def render_inference_tab():
    with gr.TabItem("Game Analysis"):
        with gr.Row():
            with gr.Column(scale=1, min_width=300):
                gr.Markdown("### Video Input")
                inf_video_in = gr.Video(label="Upload Game Video")
                
                inf_court_drp = gr.Dropdown(choices=list_courts(), label="Select Reference Court", interactive=True)
                refresh_btn = gr.Button("Refresh Courts", size="sm", scale=0)
                
                inf_run_btn = gr.Button("Run Analysis", variant="primary")
                inf_status = gr.Markdown("Ready.")

            with gr.Column(scale=3):
                gr.Markdown("### Video Output")
                with gr.Row():
                    vid_proc = gr.Video(label="AI Overlay", autoplay=True)
                    vid_mini = gr.Video(label="Minimap", autoplay=True)
                
                gr.Markdown("### Statistics")
                with gr.Row():
                    plot_poss = gr.Plot(label="Possession")
                    plot_ctrl = gr.Plot(label="Court Control")
                
                with gr.Row():
                    plot_pass = gr.Plot(label="Passes")
                    plot_intr = gr.Plot(label="Interceptions")

        refresh_btn.click(lambda: gr.Dropdown(choices=list_courts()), outputs=inf_court_drp)
        inf_run_btn.click(
            run_inference,
            inputs=[inf_video_in, inf_court_drp],
            outputs=[vid_proc, vid_mini, plot_poss, plot_ctrl, plot_pass, plot_intr, inf_status]
        )