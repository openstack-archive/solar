# Solar image building

[Atlas Vagrant Boxes (Ubuntu 14.04)](https://atlas.hashicorp.com/solar-project/boxes)
| [Docker Image (Ubuntu 14.04)](https://hub.docker.com/r/bogdando/solar-master)

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

To build for a docker (Ubuntu based), use:
```
# docker pull ubuntu:trusty
$ packer build -only=docker solar-master-docker.json
```
And for the Centos based:
```
# docker pull centos:centos7
$ packer build -only=docker solar-master-centos-docker.json
$ cd ..
$ vagrant up --provider docker
```
Note, this requires a vagrant-triggers plugin.
The minimal docker 1.10.0 version is required.

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
