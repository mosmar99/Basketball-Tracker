import cv2
import numpy as np

def warp_image(image, points, final_size=(int(1280*2), int(685*2))):
    reference_pts = np.array([[0, 0],
                              [final_size[0], 0],
                              [final_size[0], final_size[1]],
                              [0, final_size[1]]])
    
    H, _ = cv2.findHomography(points, reference_pts)
    warped_image = cv2.warpPerspective(image, H, (final_size[0], final_size[1]))
    return warped_image