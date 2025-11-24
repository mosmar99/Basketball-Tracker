import os
import threading
import requests
import tkinter as tk
from tkinter import messagebox
from shared.storage import upload_video

API_URL = "http://localhost:8000/process"
VIDEO_DIR = "./input_videos"
BUCKET_RAW = "basketball-raw-videos"

def send_request(selected_video, status_label):
    """Runs inside a thread so UI does not freeze."""
    try:
        status_label.config(text="Processing...", fg="orange")

        resp = requests.post(API_URL, params={"video_name": selected_video})

        if resp.status_code == 200:
            status_label.config(text="Done!", fg="green")
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

def start_processing(listbox, status_label):
    try:
        index = listbox.curselection()
        if not index:
            messagebox.showwarning("No selection", "Please choose a video first.")
            return

        video_name = listbox.get(index[0]).replace(".mp4", "")

        upload_raw_vid(video_name)

        # Run network call in background
        threading.Thread(
            target=send_request, args=(video_name, status_label), daemon=True
        ).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    root.title("Basketball Video Processor")
    root.geometry("400x400")

    # Title
    tk.Label(root, text="Select a video to process:", font=("Arial", 14)).pack(pady=10)

    # Listbox of videos
    listbox = tk.Listbox(root, width=40, height=10, font=("Arial", 12))
    listbox.pack(pady=5)

    # Load video names
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    videos = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")])
    for v in videos:
        listbox.insert(tk.END, v)

    # OK button
    tk.Button(
        root,
        text="OK",
        font=("Arial", 12),
        command=lambda: start_processing(listbox, status_label),
        width=10,
    ).pack(pady=10)

    # Status label
    status_label = tk.Label(root, text="", font=("Arial", 12))
    status_label.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
