import cv2
import numpy as np
import sys
sys.path.append("../")
from utils import get_width_bbox, get_center_bbox

def draw_ellipse(frame, bbox, color, track_id=None):
    y2 = int(bbox[3])
    x_center, _ = get_center_bbox(bbox)
    width = get_width_bbox(bbox)
    cv2.ellipse(frame, 
                     center=(x_center, y2), 
                     axes=(int(width), int(0.35*width)), 
                     angle=0, 
                     startAngle=-45, endAngle=235, 
                     color=color, thickness=2, lineType=cv2.LINE_4)

    rectange_width, rectangle_height = 80, 25
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