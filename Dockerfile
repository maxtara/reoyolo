FROM ubuntu:18.04

# Required so apt doesnt prompt for stuff like backups
ENV DEBIAN_FRONTEND noninteractive

ENV cwd="/home/"

WORKDIR $cwd

RUN apt update

######## Install libraries needed for opencv ########

# For some reason I couldn't install libgtk2.0-dev or libgtk-3-dev without running the 
# following line
# See https://www.raspberrypi.org/forums/viewtopic.php?p=1254646#p1254665 for issue and resolution
RUN apt-get install -y devscripts debhelper cmake libldap2-dev libgtkmm-3.0-dev libarchive-dev \
                        libcurl4-openssl-dev intltool make g++ gcc git

RUN apt-get install -y build-essential pkg-config libjpeg-dev libtiff5-dev \
                        libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
                        libxvidcore-dev libx264-dev libgtk2.0-dev libgtk-3-dev \
                        libatlas-base-dev libblas-dev libeigen3-dev liblapack-dev \
                        gfortran libpng-dev libopenexr-dev libtiff-dev libwebp-dev \
                        python3-dev python3-pip python3 python3-numpy ffmpeg

#https://stackoverflow.com/questions/37678324/compiling-opencv-with-gstreamer-cmake-not-finding-gstreamer
RUN apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
RUN apt-get install -y libavresample*
RUN apt-get install -y qt5-default
RUN apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev

#OpenGl http://www.codebind.com/linux-tutorials/install-opengl-ubuntu-linux/
RUN apt-get install -y libglu1-mesa-dev freeglut3-dev mesa-common-dev

#https://github.com/opencv/opencv/issues/12957 OpenBlas lapack
RUN apt install -y liblapacke-dev
RUN apt install -y libopenblas-dev libopenblas-base

#https://github.com/opencv/opencv/issues/8536 Opencv SFM Glog
RUN apt-get install -y libgoogle-glog-dev

#https://raspberrypi.stackexchange.com/questions/98132/how-to-install-protobuf-in-raspberrypi3-b-stretch Protobuf
RUN apt-get install -y protobuf-compiler

#https://haoyu.love/blog569.html Caffe
# RUN apt install -y caffe-cpu -- doesnt work in ubuntu 18.04

######## Pip requirements ########

RUN pip3 install -U pip
RUN pip3 install numpy requests pylint flask

######## git repos ########
RUN git clone https://github.com/opencv/opencv.git 

RUN git clone https://github.com/opencv/opencv_contrib.git 

######## Build opencv ########
RUN cd opencv && \
	mkdir build && \
	cd build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
        -D OPENCV_ENABLE_NONFREE=ON \
        -D BUILD_PERF_TESTS=OFF \
        -D BUILD_TESTS=OFF \
        -D BUILD_DOCS=ON \
        -D BUILD_EXAMPLES=ON \
        -D ENABLE_PRECOMPILED_HEADERS=OFF \
        -D BUILD_TIFF=ON \
        -D WITH_FFMPEG=ON \
        -D WITH_TBB=ON \
        -D BUILD_TBB=ON \
        -D WITH_OPENMP=ON \
        -D ENABLE_NEON=ON \
        -D ENABLE_LTO=ON \
        -D WITH_OPENCL=ON \
        -D WITH_GSTREAMER=ON \
        -D CPU_BASELINE=NEON \
        -D ENABLE_VFPV3=ON \
        -D WITH_OPENGL=ON \
        -D WITH_V4L=ON \
        -D WITH_LIBV4L=ON \
        -D WITH_QT=ON \
        -D OPENCV_EXTRA_EXE_LINKER_FLAGS=-latomic \
        -D CMAKE_SHARED_LINKER_FLAGS=-latomic \
        -D PYTHON3_EXECUTABLE=/usr/bin/python3 \
        -D PYTHON_EXECUTABLE=$(which python2) \
        .. && \
    make -j4 && make install && \
    cd ..


# Forgot to add this, and building opencv takes a long time, so this is going here
RUN pip3 install pyinotify pytest
RUN apt-get install wget
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

