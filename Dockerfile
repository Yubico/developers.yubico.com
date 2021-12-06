FROM ubuntu:18.04 AS requirements

WORKDIR /build

# drop multiverse, restricted, backports
RUN echo "deb http://archive.ubuntu.com/ubuntu/ bionic main universe" >/etc/apt/sources.list \
  && echo "deb http://archive.ubuntu.com/ubuntu/ bionic-updates main universe" >>/etc/apt/sources.list \
  && echo "deb http://archive.ubuntu.com/ubuntu/ bionic-security main universe" >>/etc/apt/sources.list

RUN apt-get -y update && apt-get -y dist-upgrade

RUN apt-get install --no-install-recommends -y \
  git \
  git-lfs \
  # for yubico-binaries repo
  openssh-client \
  python-pip \
  python-setuptools \
  asciidoc \
  mscgen \
  libffi-dev \
  libssl-dev \
  source-highlight

COPY requirements.txt ./
COPY pipcache/*.gz ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt



FROM requirements AS builder

ARG SSH_KEY

COPY .git ./.git
COPY asciidoc ./asciidoc
COPY bootstrap ./bootstrap
COPY content ./content
COPY devyco ./devyco
COPY static ./static
COPY templates ./templates
COPY .bowerrc bower.json build settings.json ./

# Build
RUN umask 0077 \
  && mkdir -p ~/.ssh \
  && echo "$SSH_KEY" > ~/.ssh/id_rsa \
  && echo "github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=" > ~/.ssh/known_hosts \
  && echo "StrictHostKeyChecking yes\nIdentitiesOnly yes\n" > ~/.ssh/config \
  && mkdir .cache \
  && rm -rf htdocs \
  && mkdir htdocs \
  && umask 0022 \
  && ./build \
  && rm ~/.ssh/id_rsa \
  && rm -rf .cache



FROM alpine:3.9

RUN apk --no-cache add apache2

# dedicated user and group
RUN addgroup -S -g 1000 www && adduser -S -u 1000 -G www www

# required for pid file
RUN mkdir -p /run/apache2 && chown www:www /run/apache2

COPY --chown=0:0 httpd.conf /etc/apache2/
COPY --from=builder --chown=0:0 /build/htdocs/dist /var/www/localhost/htdocs

EXPOSE 8080
USER 1000:1000
CMD ["httpd", "-DFOREGROUND", "-f/etc/apache2/httpd.conf"]
