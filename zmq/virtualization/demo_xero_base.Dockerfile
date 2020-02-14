FROM stackhead/ubuntu_bionic_beaver_dev

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
