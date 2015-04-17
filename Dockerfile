FROM debian:jessie
MAINTAINER Andrew Woodward awoodward@mirantis.com

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get -y install --fix-missing \
  curl \
  ssh \
  sudo \
  ansible \
  python-pip

ADD . /vagrant/
WORKDIR /vagrant

RUN ansible-playbook -i "localhost," -c local main.yml

VOLUME /vagrant