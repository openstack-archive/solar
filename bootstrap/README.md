# Solar image building

In `bootstrap/trusty64` directory there are `box.ovf` and `box-disk1.vmdk`
files from the `trusty64` Vagrant box (normally found in
 `~/.vagrant.d/boxes/trusty64/0/virtualbox`).

To build, install Packer (https://www.packer.io/):
```
cd bootstrap
packer build solar-master.json
cp solar-master.box ../
cd ..
vagrant up
```

If Vagrant throws error about `vboxsf` try this:
```
vagrant plugin install vagrant-vbguest
```
(see https://github.com/shiguredo/packer-templates/issues/16).

If you're rebuilding the same box, make sure Vagrant reimports it:
```
vagrant box remove solar-master
```