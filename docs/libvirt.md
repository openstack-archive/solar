# Using Vagrant with livbirt

First install libvirt plugin

```bash
vagrant plugin install vagrant-libvirt
```

If you do not have already vagrant box for VirtualBox, install it:

```bash
vagrant box add cgenie/solar-master
```

To use this box in libvirt you need to convert it using `vagrant-mutate` plugin:

```bash
vagrant plugin install vagrant-mutate
vagrant mutate cgenie/solar-master libvirt
```

# Use solar

``` bash
vagrant up --provider libvirt
```
