# ReoYOLO
  
### Description
A service which will provide YOLO detection of objects for reolink security cameras, and sends notifications to homeassistant.
This might be a little bespoke for others, but might be useful as an example for others.
  
Made for use with docker. 
  
reoyolo will watch the directory PROCESS_DIR for files dropped (reolink can send files) and process them.
  
## Test
```
source config.env
pytest -vs
```
  
## Run with config
```
python3 -m reoyolo config.ini
```
  
## Run with enviroment
```
export REOYOLOENV=yes
export PROCESS_DIR=/tmp/reolink/
#...etc
python3 -m reoyolo
```
  
## Docker
  
Yolo weights and models are copied to the container, but you can specify your own.
  
## Build
```
git push
docker build -t reoyolo .
docker tag reoyolo maxtara/reoyolo:latest
docker push maxtara/reoyolo
```
  
## Test
```
mkdir test_data/
# Put test files in there
docker build -t reoyolotest -f DockerfileTest .
docker run -it --rm --env-file docker.conf.env reoyolotest pytest /code/reoyolo/ -sv
docker run -it --rm --env-file docker.conf.env reoyolotest python3 -m reoyolo

# Test server
docker run -p 2224:2224 -it --rm --env-file docker.conf.env reoyolotest python3 -m reoyolo
# (might need to change port to 2224, or swap it around)
```

## Run
```
docker run -it --rm --env-file docker.conf.env reoyolo
```
  
## docker-compose
```
  reoyolo:
    image: maxtara/reoyolo
    restart: unless-stopped
    container_name: reoyolo
    user: "1000:1000"
    ports:
        - "2223:2223"
    volumes:
        - '/reo/:/data'
    environment:
        - PROCESS_DIR=/data/reolink/
        - OUTPUT_DIR=/data/reolink_out/
        - ORIG_DIR=/data/reolink_orig/
        - CUTS_DIR=/data/reolink_cuts/
        - IMAGE_URL=https://reolink.lan/cgi-bin/api.cgi?cmd=Snap&amp;channel=0&amp;rs=rs&amp;user=admin&amp;password=password
        - NOTIFY_DIR=/www/
        - YOLO_WEIGHTS_LARGE=/code/yolov4.weights
        - YOLO_CFG_LARGE=/code/yolov4.cfg
        - YOLO_WEIGHTS=/code/yolov4-tiny.weights
        - YOLO_CFG=/code/yolov4-tiny.cfg
        - YOLO_NAMES=/code/coco.names
        - DOMAIN=https://example.com.com
        - SERVICE=mobile_app_something
        - TOKEN=Bearer oawdoiajwdoij
        - REOYOLOENV=yes
```