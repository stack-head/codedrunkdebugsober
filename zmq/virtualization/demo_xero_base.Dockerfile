FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

# Start off by installing apt-utils, so it's available for all the other package installation steps.
RUN apt-get update && apt-get install -y \
    apt-utils

RUN apt-get install -y locales

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8

# Fetching, dling, extracting
RUN apt-get install -y \
    curl

RUN apt-get update && apt-get install -y \
    python3 \
    python3-distutils \
    libpython3-dev

RUN apt-get update && apt-get install -y \
    python-dateutil \
    python-zmq

# Go install pip for python3.
RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3 ./get-pip.py --upgrade && \
    pip3 install wheel --upgrade && \
    rm ./get-pip.py

WORKDIR /root/dev

COPY ./xero ./xero
RUN (cd xero && pip3 install .)
RUN (cd xero && python3 setup.py pytest)

COPY ./demo_xero ./demo_xero
RUN (cd demo_xero && pip3 install .)
