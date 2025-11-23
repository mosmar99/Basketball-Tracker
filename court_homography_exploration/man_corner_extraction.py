import cv2
import numpy as np
from ultralytics import YOLO

def point_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# Initial corner points (x, y)
points = np.array([
    [100, 100],
    [700, 100],
    [700, 500],
    [100, 500]
], dtype=np.int32)

dragging = None  # which point is being dragged (index or None)
radius = 10      # handle size

def draw_quad(img, pts, radius=5):
    overlay = img.copy()
    # Draw lines
    cv2.polylines(overlay, [pts.reshape((-1,1,2))], True, (0,255,0), 2)
    # Draw corner handles
    for (x, y) in pts:
        cv2.circle(overlay, (x, y), radius, (0,0,255), -1)
    return overlay

def mouse_callback(event, x, y, flags, param):
    global dragging, points

    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if clicking near a handle
        for i, (px, py) in enumerate(points):
            if np.hypot(px - x, py - y) < radius * 2:
                dragging = i
                break

    elif event == cv2.EVENT_MOUSEMOVE and dragging is not None:
        points[dragging] = [x, y]

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = None

cv2.namedWindow("Corner extraction, a: accept, q: quit")
cv2.setMouseCallback("Corner extraction, a: accept, q: quit", mouse_callback)

def warp_image(image, points, final_size=(int(1280*2), int(1280*2*0.3))):
    reference_pts = np.array([[0, 0],
                              [final_size[0], 0],
                              [final_size[0], final_size[1]],
                              [0, final_size[1]]])
    
    H, _ = cv2.findHomography(points, reference_pts)
    warped_image = cv2.warpPerspective(image, H, (final_size[0], final_size[1]))
    return warped_image

def draw_keypoints(image, kps):
    tmp = image.copy()
    for (x, y) in kps:
        cv2.circle(tmp, (int(x), int(y)), 4, (0,255,0), -1)

    cv2.imshow("Frame points", tmp)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def get_keypoints(res):
    keypoints = res[0].keypoints
    if keypoints is None or len(keypoints.xy) == 0:
        print("no keypoints found")
        return None
    else:
        return keypoints.xy.cpu().numpy()[0]
    
def get_points_yolo(image):
    model = YOLO("../runs/pose/train8/weights/best.pt")
    
    results_r = model.predict(source=image[:, image.shape[1]//2:], conf=0.5)
    kp_r = get_keypoints(results_r)
    draw_keypoints(image[:, image.shape[1]//2:], kp_r)

    results_l = model.predict(source=image[:, :image.shape[1]//2], conf=0.5)
    kp_l = get_keypoints(results_l)
    draw_keypoints(image[:, :image.shape[1]//2], kp_l)

def get_points_ui(image):
    global points
    warped_image = None
    cont = True

    while cont:
        display = draw_quad(image, points)
        cv2.imshow("Corner extraction, a: accept, q: quit", display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('a'):
            warped_image = warp_image(image, points)
            cont = False

    cv2.destroyAllWindows()
    cv2.imwrite("imgs/full_court_warped.jpg", warped_image)
    return warped_image

if __name__ == '__main__':
    image = cv2.imread("imgs/player_free_background_homography.jpg")
    get_points_ui(image)
    print("Corner points:\n", points)