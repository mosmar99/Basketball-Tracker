## Motivation
Within the field of professional sports, the usage of analytics to understand tactics and player performance has in recent times become increasingly widespread. Famously, the movie Moneyball (which was inspired by a real-life story), utilized sabermetrics to conduct empirical analysis of baseball games. The utilization of sabermetrics were subsequently overshadowed by the application of more sophisticated techniques, such as **machine learning** models. This project applies such techniques to basketball games.

Basketball is both dynamic and continuous in nature. Applying, for example, computer vision models to this field can prove quite rewarding, offering rich and complex data to infer analytics from.

Currently, the NBA utilizes statistics gathered by SportVU, which is a camera system that collects and provides real-time statistics such as player and ball positioning. These systems are often expensive, proprietary, or not publicly available, limiting access for smaller teams with smaller budgets or sports enthusiasts wanting to conduct their own research as a hobby.
 
Concretely, our aim is to automatically detect and track player as well as ball movement, with the intent of extracting actionable metrics from game footage. These metrics could include speed, positioning, ball possession, movement patterns and other performance indicators. The analytical results are to be without cost and immediately rendered available to its user, be it smaller organizations or hobbyists.

## General System Outline

### Minimum capabilities:
- Top-down Player court position (In MVP)
- Top-down Ball court position
- Statistics
  - Ball possession (team/individual) (In MVP)
  - Passes/Interceptions (team/individual)
- Court spatial analysis
  - Ball position heatmap
- Vizualize insights  (Partially in MVP (Video))

### Nice to have:
- Statistics
  - Goals (Individual)
  - Attempted (Individual)
- Court spatial analysis
  - Court Team Controll
- Player highlight reel

### If time permits:
- Live Analysis

### Intended tools:
- Object Detection (Ultralytics YOLOv11/SAM2 or other suitable)
- Experiment and Model Tracking (Neptune -> wandb)
- Model Registry (Neptune -> wandb)
- Id Tracking (Supervision ByteTrack or BoT-SORT)
- Homography (OpenCV SIFT, and SuperPoint + LightGlue)
- Containerization (Docker)
- Infrastructure Management (Terraform)
- Database (MongoDB for structured data storage)

### Challenges:
- Only include persons of interest (e..g, Players and Basketball), i.e., not people from the public.
- Low frequency of basketball detection. The accuracy of basketball detection is low, likely due to the relatively small basketball size. 
- Team assignment, assign which player belong to what team.
- Ball possession, specify which team (or individual) is in possession of the ball.
- Passes/Interceptions, detect pass (same team) and interception (between teams).
- Attempted/Successful shots on hoop, detect and keep track of attempted shots on hoop and or scores by team (or individuals).
- Court homography, to go from broadcast view to top down view a projection is needed. Court is obstructed by players which can be difficult for SIFT or keypoint detection.
- Packaging statistics to provide a user friendly and insightful overview.

## Pre-trained Models
Object Detection Model (baseline): [YOLOv11 (You-Only-Look-Once)](https://github.com/ultralytics/ultralytics). Although initially published in 2015, through persistent versioning of the model, it has retained its position as a state-of-the-art model. Its core strengths are its *speed*, *detection accuracy*, *good generalization*, and that its *open-source*. Each versioning of YOLO attempts to improve on the previous, be it better handling of edge cases, quicker object detection or higher accuracy.

The Object Detection task consists of two primary objectives, image recognition and image localization. Image recognition asserts whether or not there is an object of a specified type (e.g., Person) in the image. Image localization places a bounding box around the type (e..g, the Person).

The precice original implementation of YOLO is detailed in the [ORIGINAL PAPER](https://arxiv.org/pdf/1506.02640). The image is first resized into a shape of 448x448, then it goes through subsequent convolutional layers. The activation function used throughout the network is the ReLU (recitified linear unit), except in the final layer, which uses a linear activation function. In addition, regularization techniques are employed, e.g., dropout and batch normalization to prevent model overfitting.

## Experiment and Dataset
The finalized product is expected to be able to derive insights from various kinds of input videos. Although, we put some constraints on it. NBA Broadcast style video is the expected input video format. The input video format is expected to be *.mp4*.

For object detection of ball, player and referee the following dataset is used, [basketball players](https://universe.roboflow.com/workspace-5ujvu/basketball-players-fy4c2-vfsuv). The dataset contains 320 annotated images with classes: Ball, Player, Referee, Clock, Hoop, Overlay and Scoreboard. The dataset can be used to fine tune a object detection model to ignore the spectators.

For court homography a detailed writeup on Keypoint pose detetion for court is found in issue [#11](/../../issues/11) the previously specified dataset is not used (~~[a dataset with court keypoints](https://universe.roboflow.com/fyp-3bwmg/reloc2-den7l)~~). The issue also contains details on the current model and approach. The base of the current implementation is to build a panorama from video. This panorama image is used to create a reference image for keypoint extraction and matching with SuperPoint and LightGlue respectively.

Initial experiment tracking was implemented using neptune. This is currently in the progress of being migrated to weights and biases (wandb) which also provides a model registry. Progress and considerations are detailed in issue [#13](/../../issues/13). Focus has been put on getting the application to a runnable state using docker, as such model training and improvement has been put on hold during the final stages of the sprint. Since no new models have been finetuned since migration to wandb started, no experiment logs currently exist in wandb, however artifacts from neptune do. The model is kept as an artifact and linked to the model registry with tag @production. The dataset is kept in artifact storage. This is to facilitate running of the application. To access the production model from the model registry please reach out to us.

For reference, experiment tracking in neptune is shown bellow.
<img width="1908" height="551" alt="image (4)" src="https://github.com/user-attachments/assets/b2e14f9e-da37-489a-a05b-25f6c34289ea" />

For reference, model registry and current progress in wandb is shown bellow.
<img width="1140" height="535" alt="image (1)" src="https://github.com/user-attachments/assets/763472b2-2e37-4c95-877b-b0752f68efaa" />
<img width="1259" height="530" alt="image (2)" src="https://github.com/user-attachments/assets/1e3ddfe5-01a2-459e-95f7-59a5d009820d" />
<img width="1919" height="688" alt="image (3)" src="https://github.com/user-attachments/assets/2ad7f24b-71fc-4383-8504-0be2195bdc51" />

## State as of sprint 2 (MVP)
This release provides a dockerized application delivered as a Docker Compose stack consisting of five services. 
Four of these: _detector_service, team_assigner_service, court-service, and orchestrator_service_, are custom-built components developed by us, each with its own Dockerfile and image created during the build process. The fifth service, minio, is an external dependency pulled from the official minio/minio image on Docker Hub and included as part of the stack to provide object storage. The Compose stack orchestrates all five containers into a fully integrated application environment.

<img width="540" height="514" alt="bt_architecture" src="https://github.com/user-attachments/assets/4a7830ca-74ed-4626-8d1e-021597e4a74c" />

For the MVP, the client needs first install Docker and then to run "docker-compose up --build" in the WORKDIR to run all the images in containers. The client specifies local folder with videos. Then after running `python process_ui.py` in WORKDIR, is prompted with the UI (see image below).

<img width="410" height="432" alt="image" src="https://github.com/user-attachments/assets/c1ca2421-2396-4918-b3ef-1845d8224544" />

They simply specify the video to be processed, which triggers the process pipeline and is signaled by "Processing.."  keywords. When processing it completed the UI shows "Done.". Both the raw and processed videos are individually uploaded to a S3 minIO container, in individual buckets. There are unit tests in the `tests` folder to ensure that bucket video upload, video deletion and bucket deletion functions correctly.

<img width="928" height="316" alt="image" src="https://github.com/user-attachments/assets/c1e87f7d-376c-4001-b082-b93d1121f5d0" />

The orchestrator manages the whole processing pipeline, sending and recieving API (through FastAPI) calls from services. 

**A more comprehensive breakdown**: 
1. The finetuned production model for player and ball detections is found on the cloud, specifically in a model registry within weights and biases. It is amongst other reasons a cheaper option than self hosting, check [#13](/../../issues/13) for a more detailed breakdown. 
2. Subsequently the orchestrator sends the video path to the tracks detector service which returns player and ball tracks. These contain player and ball bounding boxes localizations for each player and ball object (identified by ByteTracker) across all frames.  
3. Additionally, the orchestrator sends the player tracks and the video path (note that the reference to the video is passed around to minize communication overhead) to the team assigner service. The FashionCLIP by Patrick John et al. is prompted by team jersey colors for each team and takes in a clipped version of the player bounding box and returns team group, 1 or 2. Subsequently, we implemented majority voting (for further details [#12](/../../issues/12)) over a set of frames (specifically, over 50 frames) to set the final team belonging for each object id over all frames. The result is returned to the orchestrator. Considerations were made with SAM2 without noticable improvements (see [#19](/../../pull/19)).
4. Ball acquisition run on the orchestrator service since its rule based and lightweight (i.e., does not justify a seperate service instance). It primarly utilizes to rules to check for ball position, the first being IoU and the second is based on closest distance between ball and players.
5. Thereafter, the homography matrices are calculated in the court service, which are utilized to yield accurate frame by frame updates on a minimap. The service provides homographies to reproject player coordinates for a top down view. The operation is currently ony possible on video_1.mp4 due to hardcoded reference. API is detailed in the court_service README which provides API endpoints for creating reference images. They need to be implemented into the UI to enable the option of creating reference images from any video. Detailed description of operations and previous work is found in issue [#11](/../../issues/11).
7. Lastly, within the orchestrator service, all yielded components are as an overlay drawn and depicted on the original inputted video.

The requirements file specify pytorch and NVIDIA GPU execution of models. The final product is visualized in a video below. 

https://github.com/user-attachments/assets/9a22c280-0b12-4f03-942b-536bd8b8f958

## Authors (Equal Contribution)
1. Mahmut Osmanovic
2. Isac Paulssson
3. Sebastian Tuura

---

To view a team member from our Git configuration, run:

```bash
git config --file .gitconfig --get team.member1
