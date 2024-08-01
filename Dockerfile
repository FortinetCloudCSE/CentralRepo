# syntax=docker/dockerfile:1.5-labs

#alpine has shell, busybox does not
#FROM klakegg/hugo:0.107.0-busybox AS hugo
#FROM klakegg/hugo:0.107.0-alpine AS base
FROM hugomods/hugo:std as base

FROM base as dev
ADD https://github.com/FortinetCloudCSE/CentralRepo.git#prreviewJune23 /home/CentralRepo

WORKDIR /home/CentralRepo

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

ENTRYPOINT ["/home/CentralRepo/scripts/local_copy.sh"]

FROM base as prod
ADD https://github.com/FortinetCloudCSE/CentralRepo.git#main /home/CentralRepo

WORKDIR /home/CentralRepo

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

ENTRYPOINT ["/home/CentralRepo/scripts/local_copy.sh"]
