import cv2
from PIL import Image, ImageEnhance
from transformers import CLIPProcessor, CLIPModel
from ultralytics import SAM
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

import random
import os

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


    def load_model(self):
        self.model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
        self.processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")

    def get_player_color(self,frame,bbox):
        image = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]

        # plt.imshow(image)
        # plt.axis('off')
        # plt.title("title")
        # plt.show()

        results_list = self.sam2(image, bboxes=[0, 0, int(bbox[2])-int(bbox[0]), int(bbox[3])-int(bbox[1])])
        masks_obj = results_list[0].masks  # Masks object

        if masks_obj is not None and len(masks_obj) > 0:
            mask_tensor = masks_obj.data  # torch.Tensor of shape (1, H, W)
            mask_numpy = mask_tensor[0].cpu().numpy().astype(np.uint8)


        # gray_bg = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # gray_bg = cv2.cvtColor(gray_bg, cv2.COLOR_GRAY2BGR)
        # masked_img = np.where(mask_numpy[..., None] == 1, image, gray_bg)


        # hot_pink = (255, 105, 180)  # BGR hot pink
        # hot_pink_bg = np.full_like(image, hot_pink)  # full hot pink background

        noise = np.random.randint(0, 256, image.shape, dtype=np.uint8)

        masked_img = np.where(mask_numpy[..., None] == 1, image, noise)

        #testing
        # plt.imshow(cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB))
        # plt.axis('off')
        # plt.title("title")
        # plt.show()

        rgb_image = cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB) # grayed img
        # rgba_image = np.dstack([rgb_image, mask_numpy * 255]) # transparent img

        id = random.randint(1,250)
        save_path_d = os.path.join('imgs\default', f'default_{id}.png')
        save_path_m = os.path.join('imgs\masked', f'masked{id}.png')
        plt.imsave(save_path_m, rgb_image)
        plt.imsave(save_path_d, image)

        # plt.imshow(rgba_image)
        # plt.axis('off')
        # plt.title("title")
        # plt.show()
        pil_image = Image.fromarray(rgb_image) # pytorch expects this format

        team_classes = [self.team_A, self.team_B]

        

        # inputs = self.processor(text=team_classes, images=pil_image, return_tensors="pt", padding=True)

        # outputs = self.model(**inputs)
        # logits_per_image = outputs.logits_per_image
        # max_class_prob = logits_per_image.softmax(dim=1) 

        # player_color = team_classes[max_class_prob.argmax(dim=1)[0]]

        return 0

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
        j_colors = []
        p_ids    = []
        for player_id, track in player_track.items():

            x1, y1, x2, y2 = track['bbox']
            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)
            player_crop = frame[y1:y2, x1:x2]

            results_list = self.sam2(player_crop, bboxes=[0, 0, x2-x1,y2-y1])
            masks_obj = results_list[0].masks  # Masks object

            if masks_obj is not None and len(masks_obj) > 0:
                mask_tensor = masks_obj.data  # torch.Tensor of shape (1, H, W)
                mask_numpy = mask_tensor[0].cpu().numpy().astype(np.uint8)

            noise = np.random.randint(0, 256, player_crop.shape, dtype=np.uint8)

            masked_img = np.where(mask_numpy[..., None] == 1, player_crop, noise)

            player_color = self.get_dominant_color(masked_img)
            j_colors.append(player_color)
            p_ids.append(player_id)

        team_k = 2
        team_kmeans = KMeans(n_clusters=team_k, random_state=42, n_init=10).fit(j_colors)
        team_labels = team_kmeans.labels_
        player_teams = dict(zip(p_ids, team_labels))


        for p_id, team_label in player_teams.items():
            player_assignment[frame_id][p_id] = team_label
            self.player_team_cache[player_id] = team_label

        print(player_assignment)
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
            
            player_assignment = self.assigner(player_track, vid_frames[frame_id], frame_id, player_assignment)

        #     for player_id, track in player_track.items():
        #         team = self.get_player_team(vid_frames[frame_id], track['bbox'], player_id)
        #         player_assignment[frame_id][player_id] = team
        
        save_stub(stub_path,player_assignment)

        return player_assignment