FROM debian:buster

RUN apt -y update && apt -y install npm \
  python3 \
  python3-pip \ 
  wget \
  git

RUN npm install -g diff2html-cli
RUN pip3 install requests

RUN mkdir /cargo-diff
COPY ../diff.py /cargo-diff/diff.py
COPY entrypoint.sh /cargo-diff/entrypoint.sh

WORKDIR /cargo-diff

ENTRYPOINT [".entrypoint.sh"]
