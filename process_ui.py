import os
import threading
import requests
import tkinter as tk
from tkinter import messagebox, Toplevel
from shared.storage import upload_video, download_to_temp, list_bucket_contents
import json

from client.annotate_pano import QuadPicker

API_URL = "http://localhost:8000/process"
VIDEO_DIR = "./input_videos"
BUCKET_RAW = "basketball-raw-videos"

def send_request(selected_video, reference_court, status_label):
    """Runs inside a thread so UI does not freeze."""
    try:
        status_label.config(text="Processing...", fg="orange")

        resp = requests.post(API_URL, params={"video_name": selected_video, "reference_court": reference_court})

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

def start_processing(listbox, listbox_court, status_label):
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

        # Run network call in background
        threading.Thread(
            target=send_request, args=(video_name, reference_court, status_label), daemon=True
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
    root.geometry("400x550")

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

    # OK button
    tk.Button(
        root,
        text="OK",
        font=("Arial", 12),
        command=lambda: start_processing(listbox, listbox_courts, status_label),
        width=10,
    ).pack(pady=10)

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

    # Status label
    status_label = tk.Label(root, text="", font=("Arial", 12))
    status_label.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
