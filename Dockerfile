FROM                ubuntu:14.04
MAINTAINER          Dmitry Orlov <me@mosquito.su>

RUN                 apt-get update && \
					apt-get install -y python-pip python-dev git && \
					apt-get clean

ADD                 . /tmp/build/
RUN                 pip install --upgrade --pre /tmp/build && rm -fr /tmp/build

ENTRYPOINT          /usr/bin/lumper