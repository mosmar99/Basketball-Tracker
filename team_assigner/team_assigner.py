from collections import defaultdict, deque, Counter
import cv2
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from ultralytics import SAM
import numpy as np
import random

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

    def load_model(self):
        self.model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
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

        pil_image = Image.fromarray(image) # pytorch expects this format

        if self.crop:
            # Crop the img around the center.
            pil_image = self.crop_img(pil_image)

        if self.save_imgs:
            r = random.randint(1, 1000000)
            filename = f"masked_{r}.png"
            pil_image.save(os.path.join("imgs/masked", filename))

        team_classes = [self.team_A, self.team_B]

        inputs = self.processor(text=team_classes, images=pil_image, return_tensors="pt", padding=True)

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
        
        player_color = self.get_player_color(frame,player_bbox)
        self.player_team_cache_history[player_id].append(player_color)
        team_id = self.get_team_from_history(player_id)
        print(player_id)
        return team_id

    def get_player_teams_over_frames(self, vid_frames, player_tracks):
        self.load_model()
        player_assignment=[]
        for frame_id, player_track in enumerate(player_tracks):        
            player_assignment.append({})
            
            
            for player_id, track in player_track.items():
                team = self.get_player_team(vid_frames[frame_id], track['bbox'], player_id)
                player_assignment[frame_id][player_id] = team

        return player_assignment