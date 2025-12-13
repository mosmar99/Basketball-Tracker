import cv2
import numpy as np
import sys
sys.path.append("../")
from shared.utils import get_width_bbox, get_center_bbox

def draw_square(frame, bbox, color, track_id=None):
    y2 = int(bbox[3])
    x_center, _ = get_center_bbox(bbox)
    width = get_width_bbox(bbox)
 
    sq_half = int(width * 0.7)

    front_y = y2 + 10
    back_y  = y2 - 20
 
    front_left  = (x_center - sq_half, front_y)
    front_right = (x_center + sq_half, front_y)
    back_left   = (x_center - sq_half, back_y)
    back_right  = (x_center + sq_half, back_y)
 
    cv2.line(frame, front_left, front_right, color, 2)
    cv2.line(frame, front_left, back_left, color, 2)
    cv2.line(frame, front_right, back_right, color, 2)

    rectange_width, rectangle_height = 72, 26
    x1_rect = x_center - rectange_width // 2
    x2_rect = x_center + rectange_width // 2
    y1_rect = (y2 - rectangle_height // 2) + 15
    y2_rect = (y2 + rectangle_height // 2) + 15
 
    if track_id is not None:
        cv2.rectangle(frame,
                      (int(x1_rect),int(y1_rect)),
                      (int(x2_rect),int(y2_rect)),
                      color,
                      cv2.FILLED)

        x1_text = x1_rect + 12
        if track_id > 99:
            x1_text -= 10

        cv2.putText(frame,
                    f"id: {track_id}",
                    (int(x1_text), int(y1_rect+18)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255,255,255), 2)
 
    return frame

def draw_triangle(frame, bbox, color):
    y1 = int(bbox[1])
    x_center, _ = get_center_bbox(bbox)
    triangle_points = np.array([
        [x_center,y1],
        [x_center+10,y1-20],
        [x_center-10,y1-20],
    ])
    cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
    cv2.drawContours(frame, [triangle_points], 0, (0,0,0), 2)
    return frame