import cv2
from PIL import Image, ImageEnhance
from transformers import CLIPProcessor, CLIPModel
from ultralytics import SAM
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import random

import random
import os
import torch
import umap
from umap import UMAP

import sys 
sys.path.append('../')
from utils import read_stub, save_stub

class TeamAssigner:
    def __init__(self,
                 team_A= "WHITE shirt",
                 team_B= "DARK-BLUE shirt",
                 ):
        self.team_colors = {}
        self.player_team_cache = {}        
    
        self.team_A = team_A
        self.team_B = team_B
        self.sam2 = SAM("sam2.1_b.pt")

        self.umap_reducer = UMAP(
            n_components=2,
            random_state=42,
            metric='cosine'
        )

        self.kmeans = KMeans(
            n_clusters=2,
            random_state=42,
            n_init='auto',
        )


    def load_model(self):
        self.model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
        self.processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")

    def get_player_color(self,frame,bbox):
        image = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]

        results_list = self.sam2(image, bboxes=[0, 0, int(bbox[2])-int(bbox[0]), int(bbox[3])-int(bbox[1])])
        masks_obj = results_list[0].masks  # Masks object

        if masks_obj is not None and len(masks_obj) > 0:
            mask_tensor = masks_obj.data  # torch.Tensor of shape (1, H, W)
            mask_numpy = mask_tensor[0].cpu().numpy().astype(np.uint8)

        blurred = cv2.GaussianBlur(image, (21,21), 0) 

        masked_img = np.where(mask_numpy[..., None] == 1, image, blurred)
        rgb_image = cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB) # grayed img
        pil_image = Image.fromarray(rgb_image) # pytorch expects this format

        r = random.randint(1, 1000000)
        filename = f"masked_{r}.png"
        width, height = pil_image.size
        torso_height = int(height * 0.5)
        y_center = height // 2
        y1_new = max(y_center - torso_height // 2, 0)
        y2_new = min(y_center + torso_height // 2, height)
        pil_image = pil_image.crop((0, y1_new, width, y2_new))

        pil_image.save(os.path.join("imgs/masked", filename))

        team_classes = [self.team_A, self.team_B]

        inputs = self.processor(text=team_classes, images=pil_image, return_tensors="pt", padding=True)

        outputs = self.model(**inputs)
        logits_per_image = outputs.logits_per_image
        max_class_prob = logits_per_image.softmax(dim=1) 

        player_color = team_classes[max_class_prob.argmax(dim=1)[0]]
        return player_color

    def get_player_team(self,frame,player_bbox,player_id):
        if player_id in self.player_team_cache:
          return self.player_team_cache[player_id]

        player_color = self.get_player_color(frame,player_bbox)

        team_id = 2
        if player_color == self.team_A:
            team_id = 1

        self.player_team_cache[player_id] = team_id
        return team_id
    
    def get_dominant_color(self, img, k=3):
        pixels = img.reshape(-1,3)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(pixels)
        counts = np.bincount(kmeans.labels_)
        dominant = kmeans.cluster_centers_[np.argmax(counts)]
        return dominant
    
    def assigner(self, player_track, frame, frame_id, player_assignment):
        all_embeddings = []
        p_ids    = []
        for player_id, track in player_track.items():

            x1, y1, x2, y2 = track['bbox']
            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)
            player_crop = frame[y1:y2, x1:x2]

            embedding_tensor = self.get_player_color(frame, track['bbox'])
            embedding_np = embedding_tensor.squeeze().cpu().numpy()

            all_embeddings.append(embedding_np)
            p_ids.append(player_id)
        
        if not all_embeddings:
            return player_assignment

        embeddings_matrix = np.stack(all_embeddings)

        embeddings_2d = self.umap_reducer.fit_transform(embeddings_matrix)

        cluster_labels = self.kmeans.fit_predict(embeddings_2d)

        for player_id, team_label in zip(p_ids, cluster_labels):
            team_id = team_label + 1
            player_assignment[frame_id][player_id] = team_id
            self.player_team_cache[player_id] = team_id

        return player_assignment

    def get_player_teams_over_frames(self, vid_frames, player_tracks, read_from_stub=False, stub_path=None):
        player_assignment = read_stub(read_from_stub, stub_path)
        if player_assignment is not None:
            if len(player_assignment) == len(vid_frames):
                return player_assignment

        self.load_model()
        player_assignment=[]
        for frame_id, player_track in enumerate(player_tracks):        
            player_assignment.append({})
            
            # SAFETY: clear cache in case of misclassifications
            if frame_id % 25 == 0:
                self.player_team_cache = {}
            
            # player_assignment = self.assigner(player_track, vid_frames[frame_id], frame_id, player_assignment)

            for player_id, track in player_track.items():
                team = self.get_player_team(vid_frames[frame_id], track['bbox'], player_id)
                player_assignment[frame_id][player_id] = team
        
        save_stub(stub_path,player_assignment)

        return player_assignment