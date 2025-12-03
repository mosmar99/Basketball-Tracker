import os
import json
import requests
import threading
import subprocess
import numpy as np
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from shared.storage import upload_video

API_URL = "http://localhost:8000/process"
STATS_URL = "http://localhost:8004/video_statistics"
VIDEO_DIR = "./input_videos"
BUCKET_RAW = "basketball-raw-videos"

def safe_open_url(url: str):
    try:
        if "WSL_DISTRO_NAME" in os.environ:
            win_path = url.replace("&", "^&")
            subprocess.Popen(["powershell.exe", "-Command", f"start '{win_path}'"])
            return
    except Exception:
        pass

    try:
        subprocess.Popen(["xdg-open", url])
        return
    except Exception:
        pass

    import webbrowser
    webbrowser.open(url)

def send_request(selected_video, status_label, stats_button):
    """Runs inside a thread so UI does not freeze."""
    try:
        status_label.config(text="Processing...", fg="orange")

        resp = requests.post(API_URL, params={"video_name": selected_video})

        if resp.status_code == 200:
            data = resp.json()
            ball_tp = json.loads(data["ball_tp"])
            vid_name = data["vid_name"]

            x, y = possession_to_percentages(ball_tp)
            path = possession_plot(x, y, vid_name)
            upload_img(vid_name) 

            status_label.config(text="Done!", fg="green")
            stats_button.config(state="normal")  # Enable button
        else:
            status_label.config(text="Error!", fg="red")
            messagebox.showerror("Error", f"Server returned {resp.status_code}")

    except Exception as e:
        status_label.config(text="Error!", fg="red")
        messagebox.showerror("Exception", str(e))


def upload_raw_vid(vid_name):
    local_path = f"{VIDEO_DIR}/{vid_name}.mp4"
    key = f"{vid_name}.mp4"

    uri = upload_video(local_path, key, BUCKET_NAME=BUCKET_RAW)
    print("Uploaded to:", uri)


def upload_img(vid_name):
    BUCKET_NAME = "figures"

    local_path = f"figures/ball_possession/{vid_name}.png"
    key = f"ball_possession/{vid_name}.png"

    uri = upload_video(local_path, key, BUCKET_NAME=BUCKET_NAME)

    print("Uploaded possession plot to:", uri)
    return uri


def possession_plot(x, y, video_name):
    y_percent = np.array(y) * 100
    fig, ax = plt.subplots(figsize=(14, 4))

    for i, val in enumerate(y_percent):
        ax.bar(i, val, color="#9cb2a0", width=1.0)
        ax.bar(i, 100 - val, bottom=val, color="#9eaec6", width=1.0)

    ax.plot(x, y_percent, color="black", linewidth=1)

    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, 5))
    ax.set_xlabel("Frames")
    ax.set_ylabel("Possession (%)")
    ax.set_xlim(0, len(x))

    plt.tight_layout()

    folder = "figures/ball_possession"
    os.makedirs(folder, exist_ok=True)

    filename = f"{video_name}.png"
    path = os.path.join(folder, filename)

    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path

def possession_to_percentages(ball_tp, step=0.01):
    y = []
    current = 0.5
    for team in ball_tp:
        if team == -1 and not y:
            current = 0.5
        elif team == 1 and not y:
            current = 1.0
        elif team == 2 and not y:
            current = 0.0
        else:
            if team == 1:
                current = min(current + step, 1.0)
            elif team == 2:
                current = max(current - step, 0.0)
        y.append(current)
    x = list(range(len(y)))
    return x, y

def open_stats_page(video_name):
    url = f"{STATS_URL}/{video_name}"
    print("Opening:", url)
    safe_open_url(url)


def start_processing(listbox, status_label, stats_button):
    try:
        index = listbox.curselection()
        if not index:
            messagebox.showwarning("No selection", "Please choose a video first.")
            return

        video_name = listbox.get(index[0]).replace(".mp4", "")

        upload_raw_vid(video_name)

        stats_button.config(state="disabled")

        threading.Thread(
            target=send_request,
            args=(video_name, status_label, stats_button),
            daemon=True
        ).start()

        stats_button.config(command=lambda vn=video_name: open_stats_page(vn))

    except Exception as e:
        messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    root.title("Basketball Video Processor")
    root.geometry("420x450")

    tk.Label(root, text="Select a video to process:", font=("Arial", 14)).pack(pady=10)

    listbox = tk.Listbox(root, width=40, height=10, font=("Arial", 12))
    listbox.pack(pady=5)

    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    files = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")])
    for f in files:
        listbox.insert(tk.END, f)

    process_btn = tk.Button(
        root,
        text="Process",
        font=("Arial", 12),
        command=lambda: start_processing(listbox, status_label, stats_button),
        width=12,
    )
    process_btn.pack(pady=10)

    status_label = tk.Label(root, text="", font=("Arial", 12))
    status_label.pack(pady=5)

    stats_button = tk.Button(
        root,
        text="Open Statistics Page",
        font=("Arial", 12),
        state="disabled",
        width=20,
    )
    stats_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
