FROM ubuntu:14.04

WORKDIR /

ADD bootstrap/playbooks/celery.yaml /celery.yaml
ADD resources /resources
ADD templates /templates
ADD run.sh /run.sh

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python python-dev python-distribute python-pip openssh-client rsync libyaml-dev vim libffi-dev libssl-dev git
RUN pip install ansible

RUN pip install git+https://github.com/Mirantis/solar.git
RUN pip install git+https://github.com/Mirantis/solar-agent.git

RUN ansible-playbook -v -i "localhost," -c local /celery.yaml --tags install

CMD ["/run.sh"]
