import time
import os
import urllib3
import pyinotify
from flask import Flask
import reoyolo
from reoyolo import image_processing, dirwatch, server, notify, conf, plate
import reoyolo
import uuid
import requests
from pathlib import Path
import tempfile
import shutil
import atexit
## Yea, reolink isnt the best at SSL
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEST_IMG = os.environ.get('TEST_IMG', '/tmp/testimgs/img001.jpg')
TEST_CAR_IMAGE = os.environ.get('TEST_CAR_IMAGE', '/tmp/testimgs/img001.jpg')
TEST_FOLDER =  os.environ.get('TEST_FOLDER', '/tmp/testimgs/')

# Make a copy the TEST_IMG, as we'll delete it
temp_dir = tempfile.gettempdir()
temp_path = os.path.join(temp_dir, 'tmgimg.jpg')
shutil.copy2(TEST_IMG, temp_path)
TEST_IMG = temp_path
# Make a copy the TEST_CAR_IMAGE, as we'll delete it
temp_dir2 = tempfile.gettempdir()
temp_path2 = os.path.join(temp_dir2, 'tmgimg2.jpg')
shutil.copy2(TEST_CAR_IMAGE, temp_path2)
TEST_CAR_IMAGE = temp_path2


p_small = None
p_large = None
# set up these only once because it takes  awhile.
def setup_module(module):
    global p_small, p_large
    p_small = reoyolo.processor_small.get_internal_processor() 
    p_large = reoyolo.processor_large.get_internal_processor()
    t = time.time()
    print("Warming up both processors. This can take 15 seconds")
    p_large.url_process(conf.IMAGE_URL, confidence_level=0, mask_neighbor=True)
    p_small.url_process(conf.IMAGE_URL, confidence_level=0, mask_neighbor=True)
    print(f"Warm up too {time.time() - t} seconds")

QUICK_TEST_COUNT = 10
SLOW_TEST_COUNT = 3

class TestSuite():

    # Test image processing. Other public functions are tested by url_process and file_process
    def test_image_processing(self):
        print("Checking test images")
        for file in os.listdir(TEST_FOLDER):
            filez = os.path.join(TEST_FOLDER, file)
            print(f"Testing file: {filez}")
            t = time.time()
            original_img, img, labels, confidences, cuts = p_small.file_process(filez, confidence_level=0, return_cuts=True)
            print(f"####### Done. Displaying img, took {time.time() - t} seconds. Found {labels}. {confidences}" )

        print("Testing url process small")
        for i in range(0, QUICK_TEST_COUNT):
            t = time.time()
            _, _, labels, confidences, _ = p_small.url_process(conf.IMAGE_URL, confidence_level=0, mask_neighbor=True)
            print(f"####### Done. Displaying img, took {time.time() - t} seconds. Found {labels}. {confidences}" )

        print("Testing url process large")
        for i in range(0, SLOW_TEST_COUNT):
            t = time.time()
            _, _, labels, confidences, _ = p_large.url_process(conf.IMAGE_URL, confidence_level=0, mask_neighbor=True)
            print(f"####### Done. Displaying img, took {time.time() - t} seconds. Found {labels}. {confidences}" )

        print(f"Done. \nMetrics = {p_small.get_metrics()} & {p_large.get_metrics()}.\nHistory length = {len(p_small.get_history())} & {len(p_large.get_history())}")

    def test_dirwatch_unit(self):
        # Test dirwatch
        print("Testing dirwatch function")
        t = time.time()
        original_img, img, labels, confidences, cuts = p_small.file_process(TEST_IMG, confidence_level=0.5, return_cuts=True)
        print(f"####### Done. Displaying img, took {time.time() - t} seconds. Found {labels}. {confidences}" )
        dirwatch.store_files_and_cuts(img, cuts, original_img, TEST_IMG)

    def test_dirwatcher(self):
        # Test dirwatch
        # Add a directory to the PROCESS_DIR, and check that it is now being watched
        # This is the main complex part of dirwatch.
        print("Testing dirwatcher")

        t = time.time()
        wm = pyinotify.WatchManager()
        event_handler = dirwatch.NewFileHandler(p_small, wm)
        notifier = pyinotify.ThreadedNotifier(wm, event_handler)
        print("Starting file pyinotify loop")
        notifier.start()
        try:
            time.sleep(0.2)
            olddirsetlen = len(event_handler.dir_set)
            newdirname = str(uuid.uuid4()).replace("-", "")
            Path(os.path.join(conf.PROCESS_DIR, newdirname)).mkdir(parents=True, exist_ok=True)
            time.sleep(0.2)
            open(os.path.join(conf.PROCESS_DIR, newdirname, "emptyfile"), "w").close() # This should print a warning.
            time.sleep(0.2)
            assert len(event_handler.dir_set) == olddirsetlen + 1
            print(f"Stopping file pyinotify loop")
        finally:
            try:
                
                notifier.stop()
            except:
                pass
        print(f"####### Done." )
        

    def test_notify(self):
        notify.notify("Test", "Test")
        # Static image wont be viewable from phone, as its in a private test location. Unless you mount that somewhere viewable. Probably not worth the effort though
        notify.notify_img(TEST_IMG, "bird", ["bird"], None)
        notify.notify_img(TEST_IMG, "person", ["person"], None)

    def test_server(self):
        # Clear stats
        c = server.app.test_client()
        response = c.get('/stats')
        assert response.status_code == 200

        response = c.get('/stats')
        assert response.status_code == 200
        assert response.json['count'] == 0
        assert response.json['timespent'] == 0


        p_small.history = []
        response = c.get("/reo_cvv_fast")
        assert response.status_code == 200
        assert len(response.data) > 100000 # Should be a large image

        response = c.get('/stats')
        assert response.status_code == 200
        assert response.json['count'] == 1
        assert response.json['timespent'] > 0

    def test_plates(self):
        print(f"Testing plates {TEST_CAR_IMAGE}")
        t = time.time()
        original_img, img, labels, confidences, cuts = p_small.file_process(TEST_CAR_IMAGE, confidence_level=0.5, return_cuts=True)
        print(f"####### Done. Displaying img, took {time.time() - t} seconds. Found {labels}. {confidences}" )
        dirwatch.store_files_and_cuts(img, cuts, original_img, TEST_CAR_IMAGE)

