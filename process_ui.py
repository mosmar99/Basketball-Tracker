import os
import json
import threading
import requests
import subprocess
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from tkinter import messagebox, Toplevel
from client.annotate_pano import QuadPicker
from shared.storage import upload_video, download_to_temp, list_bucket_contents, s3_upload


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


def send_request(selected_video, reference_court, status_label, stats_button):
    """Runs inside a thread so UI does not freeze."""
    try:
        status_label.config(text="Processing...", fg="orange")

        resp = requests.post(API_URL, params={"video_name": selected_video, "reference_court": reference_court})

        if resp.status_code == 200:
            data = resp.json()
            ball_tp = json.loads(data["ball_tp"])
            control_stats = json.loads(data["control_stats"])
            pi_stats = json.loads(data['pi_stats'])

            vid_name = data["vid_name"]
            x, y = possession_to_percentages(ball_tp)
            path = possession_plot(x, y, vid_name)
            s3_upload(path, f"{vid_name}.png", "figures")

            ctrl_path = control_plot(control_stats, vid_name)

            s3_upload(ctrl_path, f"{vid_name}_mm.png", "figures")

            pi_stats = [
                {
                    int(k): v
                    for k, v in frame.items()
                }
                for frame in pi_stats
            ]
            p1, p2, i1, i2 = extract_timeseries(pi_stats)
            frames = list(range(len(pi_stats)))
            passes_path = passes_plot(frames, p1, p2, vid_name)
            interceptions_path = interceptions_plot(frames, i1, i2, vid_name)

            s3_upload(passes_path, f"{vid_name}_passes.png", "figures")
            s3_upload(interceptions_path, f"{vid_name}_interceptions.png", "figures")


            status_label.config(text="Done!", fg="green")
            stats_button.config(state="normal") 
            
            status_label.config(text="Done!", fg="green")
        else:
            status_label.config(text="Error!", fg="red")
            messagebox.showerror("Error", f"Server returned {resp.status_code}")

    except Exception as e:
        status_label.config(text="Error!", fg="red")
        messagebox.showerror("Exception", str(e))

def to_percent(v1, v2):
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)

    pct = np.zeros_like(v1, dtype=float)

    for i in range(len(v1)):
        a, b = v1[i], v2[i]
        if a == 0 and b == 0:
            pct[i] = 0.5
        elif a > 0 and b == 0:
            pct[i] = 1.0
        elif a == 0 and b > 0:
            pct[i] = 0.0
        else:  # both >0
            pct[i] = a / (a + b)

    return pct

def extract_timeseries(stats):
    passes_t1 = []
    passes_t2 = []
    inter_t1 = []
    inter_t2 = []

    for frame in stats:
        t1 = frame.get(1) or frame.get("1")
        t2 = frame.get(2) or frame.get("2")

        if t1 is None or t2 is None:
            raise ValueError(f"Bad stats format: {frame}")

        passes_t1.append(t1["Passes"])
        passes_t2.append(t2["Passes"])
        inter_t1.append(t1["Interceptions"])
        inter_t2.append(t2["Interceptions"])

    return passes_t1, passes_t2, inter_t1, inter_t2

def passes_plot(frames, passes_t1, passes_t2, video_name):
    pct = to_percent(passes_t1, passes_t2)
    return percent_style_plot(
        frames, pct, video_name, label="Passes"
    )

def interceptions_plot(frames, inter_t1, inter_t2, video_name):
    pct = to_percent(inter_t1, inter_t2)
    return percent_style_plot(
        frames, pct, video_name, label="Interceptions"
    )

def percent_style_plot(x, pct_team1, video_name, label):
    y_percent = pct_team1 * 100

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color="#9eaec6", width=1.0)            
        ax_left.bar(i, 100 - val, bottom=val, color="#9cb2a0", width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=2)

    ax_left.set_ylim(0, 100)
    ax_left.set_yticks(np.arange(0, 101, 5))
    ax_left.set_ylabel(f"Team A {label} (%)")

    ax_right.set_ylim(100, 0)
    ax_right.set_yticks(np.arange(0, 101, 5))
    ax_right.set_ylabel(f"Team B {label} (%)")

    ax_left.set_xlim(0, len(x))
    ax_left.set_xlabel("Frames")

    plt.tight_layout()
    folder = f"figures/{label}"
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{video_name}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path

def possession_plot(x, y, video_name):
    y_percent = np.array(y) * 100

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color="#9eaec6", width=1.0)
        ax_left.bar(i, 100 - val, bottom=val, color="#9cb2a0", width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=2)

    ax_left.set_ylim(0, 100)
    ax_left.set_yticks(np.arange(0, 101, 5))
    ax_left.set_ylabel("Team A Possession (%)")

    ax_right.set_ylim(100, 0)
    ax_right.set_yticks(np.arange(0, 101, 5))
    ax_right.set_ylabel("Team B Possession (%)")

    ax_left.set_xlim(0, len(x))
    ax_left.set_xlabel("Frames")

    plt.tight_layout()

    folder = "figures/ball_possession"
    os.makedirs(folder, exist_ok=True)

    filename = f"{video_name}.png"
    path = os.path.join(folder, filename)

    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path

def control_plot(control_stats, video_name):
    y_percent = []
    for frame in control_stats:
        a = float(frame.get("1", 0))
        b = float(frame.get("2", 0))

        total = a + b
        if total == 0:
            y_percent.append(50)
        else:
            y_percent.append((a / total) * 100)

    y_percent = np.array(y_percent)
    x = np.arange(len(y_percent))

    fig, ax_left = plt.subplots(figsize=(14, 4))
    ax_right = ax_left.twinx()

    for i, val in enumerate(y_percent):
        ax_left.bar(i, val, color="#9cb2a0", width=1.0)
        ax_left.bar(i, 100 - val, color="#9eaec6", bottom=val, width=1.0)

    ax_left.plot(x, y_percent, color="black", linewidth=2)

    ax_left.set_ylim(0, 100)
    ax_left.set_yticks(np.arange(0, 101, 10))
    ax_left.set_ylabel("Team A Control (%)")

    ax_right.set_ylim(100, 0)
    ax_right.set_yticks(np.arange(0, 101, 10))
    ax_right.set_ylabel("Team B Control (%)")

    ax_left.set_xlim(0, len(x))
    ax_left.set_xlabel("Frames")

    plt.tight_layout()

    folder = "figures/court_control"
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"{video_name}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path

def possession_to_percentages(ball_tp):
    x = []
    y = []

    team1_count = 0
    team2_count = 0
    total_possession_frames = 0

    for i, team in enumerate(ball_tp):

        # If no possession, percentage stays the same
        if team == -1:
            # Use last known value or 50%
            if not y:
                y.append(0.5)
            else:
                y.append(y[-1])
        else:
            # Update counters
            if team == 1:
                team1_count += 1
            elif team == 2:
                team2_count += 1

            total_possession_frames = team1_count + team2_count
            team1_percentage = team1_count / total_possession_frames

            y.append(team1_percentage)

        x.append(i)

    return x, y


def open_stats_page(video_name):
    url = f"{STATS_URL}/{video_name}"
    print("Opening:", url)
    safe_open_url(url)

def upload_raw_vid(vid_name):
    local_path = f"{VIDEO_DIR}/{vid_name}.mp4"
    key = f"{vid_name}.mp4"
    uri = upload_video(local_path, key, BUCKET_NAME=BUCKET_RAW)
    print("Uploaded to:", uri)

def start_processing(listbox, listbox_court, status_label, stats_button):
    try:
        index = listbox.curselection()
        if not index:
            messagebox.showwarning("No selection", "Please choose a video first.")
            return
        
        index_court = listbox_court.curselection()
        if not index_court:
            messagebox.showwarning("No selection", "Please choose a court first.")
            return

        video_name = listbox.get(index[0]).replace(".mp4", "")
        reference_court = listbox_court.get(index_court[0])

        upload_raw_vid(video_name)

        stats_button.config(state="disabled")

        stats_button.config(command=lambda vn=video_name: open_stats_page(vn))

        # Run network call in background
        threading.Thread(
            target=send_request, args=(video_name, reference_court, status_label, stats_button), daemon=True
        ).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def call_stitch(video_name, status_label, on_done):
    try:
        status_label.config(text="Stitching...", fg="orange")

        with open(f"{VIDEO_DIR}/{video_name}.mp4", "rb") as f:
            resp = requests.post(
                "http://localhost:8003/stitch",
                files={"video": (f"{video_name}.mp4", f, "video/mp4")}
            )

        if resp.status_code == 200:
            data = resp.json()
            panorama_uri = data["panorama_uri"]

            status_label.config(text="Stitched!", fg="green")

            # trigger annotation window in main thread
            status_label.after(0, lambda: on_done(video_name, panorama_uri))

        else:
            status_label.config(text="Error", fg="red")
            messagebox.showerror("Error", f"Stitch error {resp.status_code}")

    except Exception as e:
        status_label.config(text="Error", fg="red")
        messagebox.showerror("Stitch exception", str(e))

def call_warp(panorama_uri, points, status_label):
    try:
        status_label.config(text="Warping...", fg="orange")

        resp = requests.post(
            "http://localhost:8003/warp_panorama",
            data={
                "panorama_uri": panorama_uri,
                "points_json_str": json.dumps(points)
            }
        )

        if resp.status_code == 200:
            status_label.config(text="Warped!", fg="green")
        else:
            status_label.config(text="Warp failed", fg="red")

    except Exception as e:
        status_label.config(text="Error", fg="red")
        messagebox.showerror("Warp exception", str(e))

def open_annotation(video_name, panorama_uri, status_label):
    win = Toplevel()
    win.title("Annotate Panorama")

    bucket, key = panorama_uri.replace("s3://", "").split("/", 1)
    temp_path = download_to_temp(key, bucket)

    picker = QuadPicker(win, temp_path)
    picker.pack()

    def finish():
        points = picker.get_points()
        win.destroy()

        threading.Thread(
            target=call_warp,
            args=(panorama_uri, points, status_label),
            daemon=True
        ).start()

    tk.Button(win, text="Done", command=finish).pack()

def start_stitch_annotation(listbox, listbox_courts, status_label):
    try:
        index = listbox.curselection()
        if not index:
            messagebox.showwarning("No selection", "Please choose a video first.")
            return

        video_name = listbox.get(index[0]).replace(".mp4", "")

        upload_raw_vid(video_name)

        threading.Thread(
            target=call_stitch,
            args=(video_name, status_label, lambda vn, uri: open_annotation(vn, uri, status_label)),
            daemon=True,
        ).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def list_courts(listbox):
    listbox.delete(0, tk.END)
    courts = list_bucket_contents("basketball-panorama-warp")
    for c in courts:
        listbox.insert(tk.END, c)

def main():
    root = tk.Tk()
    root.title("Basketball Video Processor")
    root.geometry("400x600")

    # Title
    tk.Label(root, text="Select a video to process:", font=("Arial", 14)).pack(pady=10)

    # Listbox of videos
    listbox = tk.Listbox(root, width=40, height=10, font=("Arial", 12), exportselection=False)
    listbox.pack(pady=5)

    # Load video names
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    videos = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")])
    for v in videos:
        listbox.insert(tk.END, v)

    tk.Label(root, text="Select a Reference Court", font=("Arial", 14)).pack(pady=10)

    # Listbox of courts
    listbox_courts = tk.Listbox(root, width=40, height=10, font=("Arial", 12), exportselection=False)
    listbox_courts.pack(pady=5)

    list_courts(listbox_courts)

    # Stats
    stats_button = tk.Button(
        root,
        text="Open Statistics Page",
        font=("Arial", 12),
        state="disabled",
        width=20,
    )

    # Court Creation
    tk.Button(
        root,
        text="Create new court",
        font=("Arial", 12),
        command=lambda: start_stitch_annotation(listbox, listbox_courts, status_label),
        width=15,
    ).pack(pady=5)

    # Refresh Court
    tk.Button(
        root,
        text="Refresh Courts",
        font=("Arial", 12),
        command=lambda: list_courts(listbox_courts),
        width=15,
    ).pack(pady=5)

    # Proccess button
    tk.Button(
        root,
        text="Proccess",
        font=("Arial", 12),
        command=lambda: start_processing(listbox, listbox_courts, status_label, stats_button),
        width=10,
    ).pack(pady=10)

    stats_button.pack(pady=10)

    status_label = tk.Label(root, text="", font=("Arial", 12))
    status_label.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()