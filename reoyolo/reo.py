# std
import uuid
import os
import sys
import shutil
import urllib3
import requests
import string
import random
import time
import io
import json
from pathlib import Path
import datetime
import pyinotify
import cv2

from reoyolo import image_processing, dirwatch, notify, conf, server
# from dirwatch import NewFileHandler, store_files_and_cuts
import reoyolo



def find_and_process_new_files(delete_after=False):
    for root, subdirs, files in os.walk(conf.PROCESS_DIR):

        # Clean up old folder. Reo also creates random 'share' folders for some reason to
        if len(files) == 0 and len(subdirs) == 0 and len(root) > len(conf.PROCESS_DIR):
            print("deleting %s" % root)
            os.rmdir(root)  # Safe folder delete
        print(root, subdirs, files)
        for new_file in files:
            f = os.path.join(root, new_file)
            if Path(f).stat().st_size == 0:
                os.remove(f)
                print("#####ZERO SIZE FILE!!!!", f)
                continue
            yield f


def process_old_file():
    count = 0
    for filez in find_and_process_new_files():
        count += 1
        t = time.time()
        print("####### Processing Old file - ", filez)
        try:
            original_img, img, labels, confidences, cuts = reoyolo.processor_small.file_process(filez, confidence_level=0, return_cuts=True)
            dirwatch.store_files_and_cuts(img, cuts, original_img, filez)
        except Exception as ex:
            raise ex
        print("####### Done. Displaying img, took %i seconds. Found %s" % (time.time() - t, labels), confidences)


def start_all():
    print("args = ", sys.argv)
    # Process files still on disk
    process_old_file()
    wm = pyinotify.WatchManager()
    event_handler = dirwatch.NewFileHandler(reoyolo.processor_small, wm)
    notifier = pyinotify.ThreadedNotifier(wm, event_handler)
    print("Starting file pyinotify loop")
    notifier.start()
    print("Starting server loop")
    server.run_server()



