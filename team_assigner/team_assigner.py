import cv2
from PIL import Image, ImageEnhance
from transformers import CLIPProcessor, CLIPModel
from ultralytics import SAM
import numpy as np
import matplotlib.pyplot as plt

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

        results_list = self.sam2(image, bboxes=[0, 0, int(bbox[2])-int(bbox[0]), int(bbox[3])-int(bbox[1])])
        masks_obj = results_list[0].masks  # Masks object

        if masks_obj is not None and len(masks_obj) > 0:
            mask_tensor = masks_obj.data  # torch.Tensor of shape (1, H, W)
            mask_numpy = mask_tensor[0].cpu().numpy().astype(np.uint8)


        gray_bg = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_bg = cv2.cvtColor(gray_bg, cv2.COLOR_GRAY2BGR)
        masked_img = np.where(mask_numpy[..., None] == 1, image, gray_bg)

        #testing
        # plt.imshow(cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB))
        # plt.axis('off')
        # plt.title("title")
        # plt.show()

        rgb_image = cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB) # grayed img
        rgba_image = np.dstack([rgb_image, mask_numpy * 255]) # transparent img
        # plt.imshow(rgba_image)
        # plt.axis('off')
        # plt.title("title")
        # plt.show()
        pil_image = Image.fromarray(rgba_image) # pytorch expects this format

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

            for player_id, track in player_track.items():
                team = self.get_player_team(vid_frames[frame_id], track['bbox'], player_id)
                player_assignment[frame_id][player_id] = team
        
        save_stub(stub_path,player_assignment)

        return player_assignment