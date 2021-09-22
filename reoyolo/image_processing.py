import collections
import time
import cv2
import numpy as np
import requests
import os
import threading
import io
from reoyolo import conf
import collections
import traceback
from reoyolo import notify

def decode_image(img):
    # Turn image into a in-memory .jpeg - suitable for sending over HTTP
    _, img2 = cv2.imencode('.JPEG', img)
    img_io = io.BytesIO(img2.tobytes())
    img_io.seek(0)
    return img_io


def save_image(img, abs_filename):
    # Write img to file.
    try:
        ret = cv2.imwrite(abs_filename, img)
        if not ret:
            raise Exception(f"Writing {abs_filename} failed for some reason")
        os.chmod(abs_filename, 0o666)
    except BaseException:
        print(traceback.format_exc())

def url_to_img(url, verify=False):
    resp = requests.get(url, stream=True, verify=verify).raw
    img = np.asarray(bytearray(resp.read()), dtype="uint8")
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

class SingleThreadedImageProcessor():
    """
    Proxy class for ImageProcessor, which locks (only one image processed at a time)
    and for a URL - returns the last image process if called within 2 seconds.
    """

    def __init__(self, *args, **kwargs):
        self.lock = threading.Lock()
        self.processor = ImageProcessor(*args, **kwargs)
        self.last_processes = 0
        self.holder = None  # Holds last processed object

    def url_process(self, *args, **kwargs):

        now = int(time.time())
        self.lock.acquire()
        if self.last_processes + 2 >= now:  # If request was made within two seconds of last process
            print("Using cache")
            ret = self.holder
        else:
            ret = self.processor.url_process(*args, **kwargs)
            self.last_processes = int(time.time())
            self.holder = ret
        self.lock.release()
        return ret

    def file_process(self, *args, **kwargs): # No cache, only lock
        self.lock.acquire()
        ret = self.processor.file_process(*args, **kwargs)
        self.lock.release()
        return ret

    def img_process(self, *args, **kwargs): # No cache, only lock
        self.lock.acquire()
        ret = self.processor.img_process(*args, **kwargs)
        self.lock.release()
        return ret


    def get_metrics(self):# no caching or locking. All pure python anyway
        return self.processor.get_metrics()

    def get_internal_processor(self):
        return self.processor

    def get_history(self):
        return self.processor.get_history()


class ImageProcessor():

    def __init__(self, large=False):
        if large:  # or ('YOLOV' in os.environ and os.environ['YOLOV'] == "large"):
            self._load_model(conf.YOLO_WEIGHTS_LARGE, conf.YOLO_CFG_LARGE, conf.YOLO_NAMES)
        else:
            self._load_model(conf.YOLO_WEIGHTS, conf.YOLO_CFG, conf.YOLO_NAMES)
        #### Metrics ####
        self.count = 0
        self.timespent = 0
        self.history = collections.deque(maxlen=20)

    def _load_model(self, weigts, config, names):
        self.net = cv2.dnn.readNet(weigts, config)
        self.classes = []
        with open(names, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]
        layer_names = self.net.getLayerNames()
        self.outputlayers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

    def _run_YOLO(self, img, mask_neighbor):
        # 1/255
        scale_factor = 0.00392

        # Size yolo model runs on
        size = (416, 416)
        if mask_neighbor: # Dont want to constantly see the neighbors cars. TODO from config
            height,width,depth = img.shape

            rec_img = np.ones((height,width), np.uint8)
            x, y, w, h = 600, 0, width-600, 110 # Neighbor's car
            cv2.rectangle(rec_img, (x, y), (x+w, y+h), 0,thickness=-1)
            x, y, w, h = 0, 0, width, 40 # Road
            cv2.rectangle(rec_img, (x, y), (x + w, y + h), 0, thickness=-1)
            x, y, w, h = 500, 0, width-500, 80 # Neighbor's driveway
            cv2.rectangle(rec_img, (x, y), (x+w, y+h), 0,thickness=-1)
            img = cv2.bitwise_and(img, img, mask=rec_img)

        blob = cv2.dnn.blobFromImage(img, scale_factor, size, (0, 0, 0), True, crop=False,)

        self.net.setInput(blob)
        outs = self.net.forward(self.outputlayers)
        return outs

    def _put_outs_on_img(self, original_img, outs, confidence_level):
        img = original_img.copy()
        height, width, channels = img.shape
        class_ids = []
        confidences = []
        boxes = []
        labels_printed = []
        used_confidences = collections.defaultdict(float)
        cuts = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > confidence_level:
                    # onject detected
                    center_x = int(detection[0]*width)
                    center_y = int(detection[1]*height)
                    w = int(detection[2]*width)
                    h = int(detection[3]*height)

                    x = int(center_x - w/2)
                    y = int(center_y - h/2)

                    boxes.append([x, y, w, h])  # put all rectangle areas
                    confidences.append(float(confidence))  # how confidence was that object detected and show that percentage
                    class_ids.append(class_id)  # name of the object tha was detected

                # Keep the highest confidence hit for each type of object.
                object_name = str(self.classes[class_id])
                used_confidences[object_name] = max(used_confidences[object_name], confidence)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, confidence_level, 0.6)

        colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        font = cv2.FONT_HERSHEY_PLAIN
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(self.classes[class_ids[i]])
                labels_printed.append(label)
                color = colors[i]
                cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
                cv2.putText(img, label, (x, y + 30), font, 1, (255, 255, 255), 2)
                cuts.append(  ( x, y, w, h, label ) )
                # print("BIT A %s on the img" % label)

        return img, set(labels_printed), used_confidences, cuts

    def img_process_1(self, original_img, confidence_level, mask_neighbor, ignore_cuts=['bench']):
        self.count += 1
        t = int(time.time())
        # Scaling down to 0.3 puts the image around the 416 mark
        img_resized = cv2.resize(original_img, None, fx=0.3, fy=0.3)
        outs = self._run_YOLO(img_resized, mask_neighbor=mask_neighbor)
        img_with_labels, labels, confidences, cuts = self._put_outs_on_img(original_img, outs, confidence_level=confidence_level)
        self.timespent += max(int(time.time()) - t, 1)  # at least 1 second.
        cuts_to_return = []

        for x, y, w, h, label in cuts:
            if label not in ignore_cuts:
                crop_img = original_img[y:y+h, x:x+w]
                cuts_to_return.append((crop_img, label))
        self.history.append(img_with_labels)
        return original_img, img_with_labels, labels, confidences, cuts_to_return

    def url_process(self, URL, verify=False, confidence_level=0.5, mask_neighbor=True, return_cuts=False):
        img = url_to_img(URL)
        return self.img_process_1(img, confidence_level, mask_neighbor=mask_neighbor)

    def img_process(self, img, confidence_level=0.5, mask_neighbor=True, return_cuts=False):
        return self.img_process_1(img, confidence_level, mask_neighbor=mask_neighbor)

    def file_process(self, file_path, verify=False, confidence_level=0.5, mask_neighbor=True, return_cuts=False):
        file_path = os.path.abspath(file_path)
        img = cv2.imread(file_path)
        return self.img_process_1(img, confidence_level, mask_neighbor=mask_neighbor)

    def get_metrics(self):
        c, t = self.count, self.timespent
        self.count = self.timespent = 0
        return c, t

    def get_history(self):
        return self.history

