FROM ubuntu:16.04

# drop multiverse, restricted, backports
RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial main universe" >/etc/apt/sources.list \
	&& echo "deb http://archive.ubuntu.com/ubuntu/ xenial-updates main universe" >>/etc/apt/sources.list \
	&& echo "deb http://archive.ubuntu.com/ubuntu/ xenial-security main universe" >>/etc/apt/sources.list

RUN apt-get -y update && apt-get -y dist-upgrade

RUN apt-get install --no-install-recommends -y \
	git \
	# for yubico-binaries repo
	openssh-client \
	python-pip \
	python-setuptools \
	asciidoc \
	mscgen \
	libffi-dev \
	libssl-dev \
	source-highlight

COPY requirements.txt /
COPY pipcache/*.gz  /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

ARG uid
ARG gid

# MacOS default user's primary group has GID=20.
#
# Ubuntu container 'dialout' group also has GID=20;
#
#   jean@thinkpad:~$ docker run --rm -it ubuntu:16.04
#   root@3bb92dbf5716:/# getent group 20
#   dialout:x:20:
#
# Change container's 'dialout' GID to avoid conflict;
#
#   root@3bb92dbf5716:/# groupmod -g 9000 dialout
#   root@3bb92dbf5716:/# getent group dialout
#   dialout:x:9000:
#
# NOTE: files owned by dialout group won't automatically be updated to GID=9000,
#   meaning a new group with GID=20 will gain group ownership on such pre-existing files.
#
# This shouldn't be a problem as typically 'dialout' is the group owner of /dev/tty*,
#   and TTY devices shouldn't be available within this container.
RUN groupmod -g 9000 dialout

RUN addgroup --gid $gid build
RUN adduser --home /home/build --shell /bin/bash --disabled-login --gecos '' \
    --uid $uid --gid $gid \
    build

USER build

VOLUME /developers
WORKDIR /developers

CMD ["./build"]
