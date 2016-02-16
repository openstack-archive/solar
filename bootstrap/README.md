# Solar image building

[Atlas Vagrant Boxes (Ubuntu 14.04)](https://atlas.hashicorp.com/solar-project/boxes)
| [Docker Image (Ubuntu 14.04)](https://hub.docker.com/r/bogdando/solar-master)

Building on the host OS
-----------------------

To build for a Virtualbox, install Packer (https://www.packer.io/):
```
$ cp vagrant-settings.yaml_defaults vagrant-settings.yaml
$ sed -i 's/master_image:.*$/master_image: solar-master/g' ./vagrant-settings.yaml
$ sed -i 's/slaves_image:.*$/slaves_image: solar-master/g' ./vagrant-settings.yaml
$ cd bootstrap
$ packer build -only=virtualbox-iso solar-master.json
$ mv solar-master-virtualbox.box ../solar-master.box
$ cd ..
$ vagrant box add solar-master solar-master.box --provider virtualbox
$ vagrant up --provider virtualbox
```

To build for a libvirt, replace the following commands:
```
$ packer build -only=qemu solar-master.json
$ mv solar-master-libvirt.box ../solar-master.box
$ cd ..
$ vagrant box add solar-master solar-master.box --provider libvirt
$ vagrant up --provider libvirt

```
Note, this requires a vagrant-libvirt plugin.

To build for a docker, use:
```
# docker pull ubuntu:trusty
$ packer build -only=docker solar-master-docker.json
$ cd ..
$ vagrant up --provider docker
```
Note, this requires a vagrant-triggers plugin.
The minimal docker 1.10.0 version is required.

Building in the docker container
--------------------------------

Here is an example builder docker image how-to guide for the `Fedora:latest`.
Note, that you will need the docker >=1.10.0 and we assume the current
user to be included into the docker group to skip sudoing.

First, get a builder container up and ruinning:
```
$ docker pull fedora
$ docker run -v /sys/fs/cgroup:/sys/fs/cgroup \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v <your_path_to_clonned_solar_repo>:/solar \
  -v /tmp:/tmp --privileged -h builder -it fedora bash
```
Adjust the ``your_path_to_clonned_solar_repo`` as apropriate.
You can access build artifacts by that path later as well.
These mountpoints pass the host OS docker services to nested containers
and also resolve packer tmp dir mount issues for nested dockers.
Note, for the packer >=0.9.0, use ``-v /tmp:/root/.packer.d/tmp`` instead.

Second, setup Docker and misc build requirements:
```
# yum install sudo autoconf gcc-c++ curl wget unzip libvirt qemu
# curl -sSL https://get.docker.com/ | sh
```

Next, install Packer to the builder container:
```
# PACKER_VERSION=0.8.6
# mkdir -p /opt/packer && cd /opt/packer
# wget --no-verbose https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip
# unzip packer_${PACKER_VERSION}_linux_amd64.zip -d /opt/packer && rm -f packer_${PACKER_VERSION}_linux_amd64.zip
# cd /usr/bin && ln -s /opt/packer/* . && cd /root
```

You may want to commit and tag here to get a clean state for the builder container.

At last, you can build images with packer. For example:
```
# cd /solar/bootstrap
# export PATH=/usr/bin:$PATH
# PACKER_LOG=1 headless=true packer build -only=docker -color=false solar-master-ubuntu-docker.json
# PACKER_LOG=1 headless=true packer build -only=docker -color=false solar-master-centos-docker.json
```
Note, the custom path workarounds conflicting Fedora's ``/usr/sbin/packer``
and the packer binary we want to use here.

You may as well reuse the pre-built builder container, for example:
TODO(bogdando) replace to the solar-project
```
$ docker pull bogdando/solar-packer-builder
$ docker run -v /sys/fs/cgroup:/sys/fs/cgroup \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v <your_path_to_clonned_solar_repo>:/solar \
  -v /tmp:/tmp --privileged -h builder -it bogdando/solar-packer-builder bash
# cd /solar/bootstrap
# export PATH=/usr/bin:$PATH
# PACKER_LOG=1 headless=true packer build -only=qemu -color=false solar-master.json
```

Troubleshooting
---------------

If Vagrant throws error about `vboxsf` try this:
```
$ vagrant plugin install vagrant-vbguest
```
(see https://github.com/shiguredo/packer-templates/issues/16).

If you're rebuilding the same box, make sure Vagrant reimports it:
```
$ vagrant box remove solar-master
```

Note that you can also set `PACKER_LOG=debug` and/or `VAGRANT_LOG=debug`
the shell environment variables to get more information.
