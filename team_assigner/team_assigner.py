from collections import defaultdict, deque, Counter
import cv2
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from ultralytics import SAM
import numpy as np
import random
from time import time
import torch

import os

import sys 
sys.path.append('../')

class TeamAssigner:
    def __init__(self,
                 team_A= "WHITE shirt",
                 team_B= "DARK-BLUE shirt",
                 history_len = 50,
                 crop_factor = 0.375,
                 save_imgs = False,
                 crop = False
                 ):
        self.team_colors = {}
        self.history_len = history_len
        self.player_team_cache_history = defaultdict(lambda: deque(maxlen=history_len))

        self.crop_factor = crop_factor
        self.save_imgs = save_imgs
        self.crop = crop
    
        self.team_A = team_A
        self.team_B = team_B
        
        self.load_model()

    def load_model(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")

    def crop_img(self, pil_image):
        width, height = pil_image.size
        torso_height = int(height * self.crop_factor)
        y_center = height // 2
        y1_new = max(y_center - torso_height // 2, 0)
        y2_new = min(y_center + torso_height // 2, height)
        cropped_pil_image = pil_image.crop((0, y1_new, width, y2_new))

        return cropped_pil_image

    def get_player_color(self,frame,bbox):
        image = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]

        pil_image = Image.fromarray(image)

        if self.crop:
            pil_image = self.crop_img(pil_image)

        if self.save_imgs:
            r = random.randint(1, 1000000)
            filename = f"masked_{r}.png"
            pil_image.save(os.path.join("imgs/masked", filename))

        team_classes = [self.team_A, self.team_B]

        inputs = self.processor(text=team_classes, images=pil_image, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        logits_per_image = outputs.logits_per_image
        max_class_prob = logits_per_image.softmax(dim=1) 

        player_color = team_classes[max_class_prob.argmax(dim=1)[0]]
        return player_color

    def get_team_from_history(self, player_id):
        history = list(self.player_team_cache_history[player_id])
        
        if not history:
            return None
        
        counter = Counter(history)
        most_freq, _ = counter.most_common(1)[0]
        print(counter)
        print(most_freq)
        return 1 if most_freq == self.team_A else 2

    def get_player_team(self,frame,player_bbox,player_id):
        start = time()
        player_color = self.get_player_color(frame,player_bbox)
        self.player_team_cache_history[player_id].append(player_color)
        team_id = self.get_team_from_history(player_id)
        print(player_id)
        return team_id
    
    def get_player_color_batch(self, pil_images):
        team_classes = [self.team_A, self.team_B]

        inputs = self.processor(
            text=team_classes,
            images=pil_images,
            return_tensors="pt",
            padding=True
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        pred_indices = probs.argmax(dim=1).tolist()
        return [team_classes[i] for i in pred_indices]
    
    def process_frame_batched(self, frame, player_track):
        pil_images = []
        player_ids = []
        bboxes = []

        for pid, info in player_track.items():
            bbox = info['bbox']
            crop = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
            pil_img = Image.fromarray(crop)

            if self.crop:
                pil_img = self.crop_img(pil_img)

            if self.save_imgs:
                r = random.randint(1, 1_000_000)
                pil_img.save(f"imgs/masked/masked_{r}.png")

            pil_images.append(pil_img)
            player_ids.append(pid)
            bboxes.append(bbox)

        predicted_colors = self.get_player_color_batch(pil_images)

        assignment = {}
        for pid, color in zip(player_ids, predicted_colors):
            self.player_team_cache_history[pid].append(color)
            assignment[pid] = self.get_team_from_history(pid)

        return assignment

    def get_player_teams_over_frames(self, vid_frames, player_tracks):
        player_assignment = []

        for frame_id, player_track in enumerate(player_tracks):
            frame = vid_frames[frame_id]
            assignment = self.process_frame_batched(frame, player_track)
            player_assignment.append(assignment)

        return player_assignment