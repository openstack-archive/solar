FROM ubuntu:14.04

WORKDIR /

RUN apt-get update
RUN apt-get install -y python python-dev python-distribute python-pip openssh-client rsync
RUN pip install ansible

ADD bootstrap/playbooks/celery.yaml /celery.yaml
ADD resources /resources
ADD templates /templates
ADD run.sh /run.sh

RUN apt-get update
RUN apt-get install -y python python-dev python-distribute python-pip \
    libyaml-dev vim libffi-dev libssl-dev git
RUN pip install ansible

RUN pip install git+https://github.com/Mirantis/solar.git
RUN pip install git+https://github.com/Mirantis/solar-agent.git

RUN ansible-playbook -v -i "localhost," -c local /celery.yaml --tags install

CMD ["/run.sh"]
