FROM ubuntu:14.04

WORKDIR /

RUN apt-get update
# Install pip's dependency: setuptools:
RUN apt-get install -y python python-dev python-distribute python-pip
RUN pip install ansible

ADD bootstrap/playbooks/celery.yaml /celery.yaml
ADD resources /resources
ADD templates /templates
ADD run.sh /run.sh


RUN apt-get install -y libffi-dev libssl-dev
RUN pip install https://github.com/Mirantis/solar/archive/master.zip
RUN pip install https://github.com/Mirantis/solar-agent/archive/master.zip

RUN ansible-playbook -v -i "localhost," -c local /celery.yaml --tags install

CMD ["/run.sh"]
