import tkinter as tk
from PIL import Image, ImageTk

class QuadPicker(tk.Frame):
    def __init__(self, parent, image_path, max_display_size=1000):
        super().__init__(parent)

        # Load full-res image
        self.img_full = Image.open(image_path)
        self.full_w, self.full_h = self.img_full.size

        # Fit to screen
        self.scale = min(max_display_size / self.full_w,
                         max_display_size / self.full_h,
                         1.0)

        disp_w = int(self.full_w * self.scale)
        disp_h = int(self.full_h * self.scale)

        self.img_disp = self.img_full.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(self.img_disp)

        # Canvas
        self.canvas = tk.Canvas(self, width=disp_w, height=disp_h)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # State
        self.points = []        # original coordinates (floats)
        self.point_ids = []     # ovals
        self.label_ids = []     # text labels
        self.line_ids = []      # connecting lines
        self.drag_index = None  # index of point being dragged

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
    
    def get_points(self):
        return self.points

    def on_click(self, event):
        dx, dy = event.x, event.y

        for i, oid in enumerate(self.point_ids):
            x1, y1, x2, y2 = self.canvas.coords(oid)
            if x1 <= dx <= x2 and y1 <= dy <= y2:
                self.drag_index = i
                return

        if len(self.points) < 4:
            ox = dx / self.scale
            oy = dy / self.scale
            self.points.append((ox, oy))

            oval_id, label_id = self._draw_point(dx, dy, len(self.points))
            self.point_ids.append(oval_id)
            self.label_ids.append(label_id)

            self._redraw_lines()

    def on_drag(self, event):
        if self.drag_index is None:
            return

        dx, dy = event.x, event.y

        r = 6
        self.canvas.coords(
            self.point_ids[self.drag_index],
            dx-r, dy-r, dx+r, dy+r
        )

        self.canvas.coords(
            self.label_ids[self.drag_index],
            dx + 10, dy
        )

        self.canvas.tag_raise(self.point_ids[self.drag_index])
        self.canvas.tag_raise(self.label_ids[self.drag_index])

        ox = dx / self.scale
        oy = dy / self.scale
        self.points[self.drag_index] = (ox, oy)

        self._redraw_lines()

    def on_release(self, event):
        self.drag_index = None

    def _draw_point(self, dx, dy, index):
        r = 6
        oval_id = self.canvas.create_oval(dx-r, dy-r, dx+r, dy+r, fill="red")
        label_id = self.canvas.create_text(dx + 10, dy, text=str(index), fill="white", anchor="w", font=("Arial", 12, "bold"))

        self.canvas.tag_raise(oval_id)
        self.canvas.tag_raise(label_id)

        return oval_id, label_id

    def _redraw_lines(self):
        for lid in self.line_ids:
            self.canvas.delete(lid)
        self.line_ids.clear()

        n = len(self.points)
        if n < 2:
            return

        for i in range(n - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            lid = self.canvas.create_line(x1 * self.scale, y1 * self.scale, x2 * self.scale, y2 * self.scale, fill="red", width=2)
            self.line_ids.append(lid)

        if n == 4:
            x1, y1 = self.points[3]
            x2, y2 = self.points[0]
            lid = self.canvas.create_line(x1 * self.scale, y1 * self.scale, x2 * self.scale, y2 * self.scale, fill="red", width=2)
            self.line_ids.append(lid)

if __name__ == "__main__":
    root = tk.Tk()
    QuadPicker(root, "court_homography_exploration/imgs/player_free_background_homography.jpg", max_display_size=1200).pack()
    root.mainloop()