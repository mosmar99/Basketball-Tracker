## Motivation
Within the field of professional sports, the usage of analytics to understand tactics and player performance has in recent times become increasingly widespread. Famously, the movie Moneyball (which was inspired by a real-life story), utilized sabermetrics to conduct empirical analysis of baseball games. The utilization of sabermetrics were subsequently overshadowed by the application of more sophisticated techniques, such as **machine learning** models. This project applies such techniques to basketball games.

Basketball is both dynamic and continuous in nature. Applying, for example, computer vision models to this field can prove quite rewarding, offering rich and complex data to infer analytics from.

Currently, the NBA utilizes statistics gathered by SportVU, which is a camera system that collects and provides real-time statistics such as player and ball positioning. These systems are often expensive, proprietary, or not publicly available, limiting access for smaller teams with smaller budgets or sports enthusiasts wanting to conduct their own research as a hobby.
 
Concretely, our aim is to automatically detect and track player as well as ball movement, with the intent of extracting actionable metrics from game footage. These metrics could include speed, positioning, ball possession, movement patterns and other performance indicators. The analytical results are to be without cost and immediately rendered available to its user, be it smaller organizations or hobbyists.

## General System Outline

### Minimum capabilities:
- Top-down Player court position
- Top-down Ball court position
- Statistics
  - Ball possession (team/individual)
  - Passes/Interceptions (team/individual)
- Court spatial analysis
  - Ball position heatmap
- Vizualize insights

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
- Experiment Tracking (MLFlow)
- Model Repository (MLFlow)
- Id Tracking (Supervision ByteTrack or BoT-SORT)
- Homography (OpenCV SIFT or other suitable keypoint detection model)
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

## Datasets
The finalized product is expected to be able to derive insights from various kinds of input videos. Although, we put some constraints on it. NBA Broadcast style video is the expected input video format. The input video format is expected to be *.mp4*.

For object detection of ball, player and referee the following dataset is used, [basketball players](https://universe.roboflow.com/workspace-5ujvu/basketball-players-fy4c2-vfsuv). The dataset contains 320 annotated images with classes: Ball, Player, Referee, Clock, Hoop, Overlay and Scoreboard. The dataset can be used to fine tune a object detection model to ignore the spectators. Additionally, if SIFT does not work for court homography, [a dataset with court keypoints](https://universe.roboflow.com/fyp-3bwmg/reloc2-den7l) exists. This enables us to train a model to detect keypoints for perspective transform calculation.

## Authors (Equal Contribution)
1. Mahmut Osmanovic
2. Isac Paulssson
3. Sebastian Tuura

---

To view a team member from our Git configuration, run:

```bash
git config --file .gitconfig --get team.member1
