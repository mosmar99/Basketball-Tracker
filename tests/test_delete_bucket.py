from shared.storage import delete_bucket

def test_del_bucket():
    uri = delete_bucket(BUCKET_NAME="basketball")
    print("Content at:", uri, "has been deleted.")

if __name__ == "__main__":
    test_del_bucket()