from flask import send_file
from flask import Flask
from flask import request
from flask import jsonify
from flask import request
# from image_processing import SingleThreadedImageProcessor, image_processing.decode_image, reoyolo.decode_image, reoyolo.processor_large
from reoyolo import image_processing, conf
import reoyolo
import glob
import os
import time
from pathlib import Path
# Flask server create. Doesnt start it
app = Flask(__name__)
counter = 3

@app.route("/reo_cvv_fast")
def reo_cvv_fast():
    confidence = request.args.get('confidence', default=5, type=int) / 10  # 0-10 accepted, turns to 0.0 to 1.0
    _, img_io, _, _, _ = reoyolo.processor_small.url_process(conf.IMAGE_URL, confidence_level=confidence)
    return send_file(image_processing.decode_image(img_io), mimetype='image/jpeg')


@app.route("/reo_cvv_slow")
def reo_cvv_slow():
    confidence = request.args.get('confidence', default=5, type=int) / 10  # 0-10 accepted, turns to 0.0 to 1.0
    _, img_io, _, _, _ = reoyolo.processor_large.url_process(conf.IMAGE_URL, confidence_level=confidence)
    return send_file(image_processing.decode_image(img_io), mimetype='image/jpeg')


@app.route("/stats_fast")
def stats_fast():
    count, timespent = reoyolo.processor_small.get_metrics()
    return jsonify({"count": count, "timespent": timespent})


@app.route("/stats_slow")
def stats_slow():
    count, timespent = reoyolo.processor_large.get_metrics()
    return jsonify({"count": count, "timespent": timespent})


@app.route("/stats")
def stats():
    count1, timespent1 = reoyolo.processor_small.get_metrics()
    count2, timespent2 = reoyolo.processor_large.get_metrics()
    return jsonify({"count": count1+count2, "timespent": timespent1 + timespent2})

@app.route("/latest")
def latest():
    global counter
    history = reoyolo.processor_small.get_history()

    # no history yet, probably just started. So just do a quick process right now, and re-get history
    if len(history) == 0:
        reoyolo.processor_small.url_process(conf.IMAGE_URL, confidence_level=0)
        history = reoyolo.processor_small.get_history()
    counter += 1
    counter = counter % len(history)
    img_io = history[counter]
    time.sleep(1)
    return send_file(image_processing.decode_image(img_io), mimetype='image/jpeg')

@app.route("/raw")
def raw():
    resp = image_processing.raw_url(conf.IMAGE_URL)
    return send_file(resp, mimetype='image/jpeg')

def run_server():
    app.run(port=2223, host="0.0.0.0")
