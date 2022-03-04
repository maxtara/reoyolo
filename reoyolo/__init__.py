from reoyolo import notify
from reoyolo import conf
from reoyolo import image_processing
from reoyolo import dirwatch
from reoyolo import reo
import os
import sys

configMap = {}
# update config from enviroment, or from a config.ini, depending if REOYOLOENV is set.
if "REOYOLOENV" in os.environ:
    configMap = os.environ
elif len(sys.argv) > 1 and os.path.exists(sys.argv[1]): 
    import configparser
    config = configparser.ConfigParser()                                     
    config.read(sys.argv[1])
    configMap = config['DEFAULT']
else:
    print("Argument 1 doesnt exist, or is not a ini config file, and REOYOLOENV not set. Exiting")
    exit(1)

conf.PROCESS_DIR = configMap['PROCESS_DIR']
conf.OUTPUT_DIR = configMap['OUTPUT_DIR']
conf.ORIG_DIR = configMap['ORIG_DIR']
conf.CUTS_DIR = configMap['CUTS_DIR']
conf.IMAGE_URL = configMap['IMAGE_URL']
conf.NOTIFY_DIR = configMap['NOTIFY_DIR']
conf.YOLO_WEIGHTS_LARGE = configMap['YOLO_WEIGHTS_LARGE']
conf.YOLO_CFG_LARGE = configMap['YOLO_CFG_LARGE']
conf.YOLO_WEIGHTS = configMap['YOLO_WEIGHTS']
conf.YOLO_CFG = configMap['YOLO_CFG']
conf.YOLO_NAMES =  configMap['YOLO_NAMES'] 
conf.DOMAIN = configMap['DOMAIN']
conf.TOKEN = configMap['TOKEN']

processor_small = image_processing.SingleThreadedImageProcessor()
processor_large = image_processing.SingleThreadedImageProcessor(large=True)


def main():
    reo.start_all()