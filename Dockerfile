FROM ubuntu:latest

# Required so apt doesnt prompt for stuff like backups
ENV DEBIAN_FRONTEND noninteractive

ENV cwd="/home/"

WORKDIR $cwd

RUN apt update

# Install binaries
RUN apt-get install -y \
    libopencv-dev \
    python3-dev \
    python3-numpy \
    python3-opencv \
    python3-pip \
    wget \
    curl


# Dev pip3 modules
RUN pip3 install pyinotify pytest requests pylint "urllib3<2"

# Get the yolo weights
RUN mkdir /code
RUN wget https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4.cfg -O /code/yolov4.cfg
RUN wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights -O /code/yolov4.weights
RUN wget https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg -O /code/yolov4-tiny.cfg
RUN wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights -O /code/yolov4-tiny.weights
RUN wget https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/coco.names -O /code/coco.names


# Code last, change this the most
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache
RUN python3 -m pip install https://github.com/maxtara/reoyolo/archive/master.zip


# webserver port
EXPOSE 2223

# Run
CMD ["python3","-m", "reoyolo"]
