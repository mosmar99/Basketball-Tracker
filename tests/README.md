**Details:**
- `test_a_connectivity.py`: checks the statuses of the services by the new ping endpoint.
- `test_b_video_pipeline.py`: takes the small video, and uploads it to the miniobucket, then does the entire processing including minimap, team_assignment, tracks, drawing etc.
- `test_end_to_end_panorama.py`: takes the same video again and firstly stitches and then wraps it.
- `test_mongodb.py`: similarly to the test_a_connectivity.py test it checks whether we are able to connect, this time to mongodb
- `test_z_cleanup.py`: tests delete operations in all the buckets, except one specific for figures in minio. Deleting everything created in the previous tests, acting as a cleanup in the process.

**How to run tests**

Run all tests:
```py
    # From project dir
    python tests/main.py
```

Run a specific test:
```py
    # From project dir
    python -m tests.TESTNAME
    # where test name is the name of the specific file.
```