import os
import threading
import requests
import tkinter as tk
import subprocess
from tkinter import messagebox
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

    # Load videos
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    files = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")])
    for f in files:
        listbox.insert(tk.END, f)

    # Process Button
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

    # Stats Button (disabled until processing is done)
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
