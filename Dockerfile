FROM ubuntu:xenial
RUN apt-get -qq update && apt-get -qq upgrade && apt-get install -qq python-pip git asciidoc mscgen libffi-dev libssl-dev source-highlight
RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir -p /working /dest
VOLUME /working /dest

CMD (cd /working && ./build)
