from shared import delete_video, list_bucket_contents
from services.ui_service import config

VIDEO = config.VIDEO

def test_main():

    video_name = VIDEO.replace('.mp4', '')
    court = video_name + '.jpg'

    delete_video(VIDEO, BUCKET_NAME=config.BUCKET_RAW)
    delete_video(VIDEO, BUCKET_NAME=config.BUCKET_PROCESSED)
    delete_video(VIDEO, BUCKET_NAME=config.BUCKET_MINIMAP)
    delete_video(court, BUCKET_NAME=config.BUCKET_COURTS)
    delete_video(court, BUCKET_NAME=config.BUCKET_COURT_P)

    contents = []
    contents.append(list_bucket_contents(config.BUCKET_RAW))
    contents.append(list_bucket_contents(config.BUCKET_PROCESSED))
    contents.append(list_bucket_contents(config.BUCKET_MINIMAP))
    contents.append(list_bucket_contents(config.BUCKET_COURTS))
    contents.append(list_bucket_contents(config.BUCKET_COURT_P))

    all_successful = True
    for content in contents:
        if VIDEO in content or court in content:
            all_successful = False

    
    assert(all_successful)


if __name__ == "__main__":
    test_main()