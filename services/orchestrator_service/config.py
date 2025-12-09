import os
from dataclasses import dataclass

@dataclass(frozen=True)
class ServiceConfig:
    detector_url: str
    assigner_url: str
    homography_url: str

def load_config():
    return ServiceConfig(
        detector_url=os.getenv("DETECTOR_URL", "http://detector_service:8000/track"),
        assigner_url=os.getenv("TEAM_ASSIGNER_URL", "http://team_assigner_service:8000/assign_teams"),
        homography_url=os.getenv("HOMOGRAPHY_URL", "http://court-service:8000/homographyvideo"),
    )

CONFIG = load_config()

