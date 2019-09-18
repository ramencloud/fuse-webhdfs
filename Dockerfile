FROM buildpack-deps:xenial
RUN { \
        echo deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu xenial main; \
        echo deb-src http://ppa.launchpad.net/deadsnakes/ppa/ubuntu xenial main; \
    } > /etc/apt/sources.list.d/deadsnakes.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
RUN apt update && apt install -y python3.7-dev
ADD https://bootstrap.pypa.io/get-pip.py get-pip.py
RUN python3.7 get-pip.py
COPY . fuse-webhdfs/
WORKDIR fuse-webhdfs
RUN pip3 install -r requirements.txt
RUN pip3 install pyinstaller
RUN pyinstaller --onefile mount-webhdfs.py
