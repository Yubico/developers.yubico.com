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

CMD ["./build"]
