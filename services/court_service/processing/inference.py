import cv2
import torch
import numpy as np

from lightglue import SuperPoint, LightGlue

class HomographyInference:
    def __init__(self, device):
        self.extractor = SuperPoint(pretrained=True).eval().to(device)
        self.matcher = LightGlue(pretrained='superpoint').eval().to(device)
        self.device = device

    def estimate_court_homography(self, frame, reference):
        gray_base = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

        torch_base = torch.from_numpy(gray_base)[None, None].to(self.device)
        torch_frame = torch.from_numpy(gray_frame)[None, None].to(self.device)

        feats0 = self.extractor.extract(torch_base)
        feats1 = self.extractor.extract(torch_frame)
        matches = self.matcher({'image0': feats0, 'image1': feats1})

        m0 = matches['matches0'][0].cpu().numpy()
        valid = m0 > -1

        mkpts0 = feats0['keypoints'][0][valid].cpu().numpy()
        mkpts1 = feats1['keypoints'][0][m0[valid]].cpu().numpy()

        if len(mkpts0) >= 4:
            H, _ = cv2.findHomography(mkpts1, mkpts0, cv2.RANSAC, ransacReprojThreshold=200)

        return H
        
