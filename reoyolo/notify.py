from requests import post
import os
import time
from reoyolo import conf

def now():
    return int(time.time())

class Throttler:
    def __init__(self):
        self.RATE = 5.0
        self.PER = 120.0
        self.allowance = self.RATE
        self.last_check = now()

    def is_allowed(self):
        self.current = now()
        self.time_passed = self.current - self.last_check
        self.last_check = self.current
        self.allowance += self.time_passed * (self.RATE / self.PER)
        if (self.allowance > self.RATE):
            self.allowance = self.RATE
        if (self.allowance < 1.0):
            return False
        else:
            self.allowance -= 1.0
            return True

HASSIO_THROTTLER = Throttler()

OBJECT_BLACKLIST = [
    "bird", "book", "bottle", "pottedplant", "elephant", "laptop", "mouse", "surfboard"
]

def notify_img(path, object_type, objects):
    only_blacklist = True
    for o in objects:
        if o not in OBJECT_BLACKLIST:
            only_blacklist = False

    if only_blacklist:
        print(str(objects) + " contains only blacklisted items, not notifying ")
        return
    else:
         print(str(objects) + " - All good, notifying")


    if not HASSIO_THROTTLER.is_allowed():
        return
    data = {
        "message": "A wild %s appeared" % object_type,
        "data": {
            "image": conf.DOMAIN + '/local/' + path
        }
    }
    # Not going to raise if this fails, because it's not critical
    post(f"{conf.DOMAIN}/api/services/notify/notify", headers={'Authorization': conf.TOKEN,'content-type': 'application/json'}, json=data)


def notify(title, message):
    if not HASSIO_THROTTLER.is_allowed():
        return
    data = {
        "message": message,
        "title": title
    }
    # Not going to raise if this fails, because it's not critical
    post(f"{conf.DOMAIN}/api/services/notify/notify", headers={'Authorization': conf.TOKEN,'content-type': 'application/json'}, json=data)
