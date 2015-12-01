# Using Vagrant with livbirt

First install libvirt plugin

```bash
vagrant plugin install vagrant-libvirt
```

If you do not have already vagrant box for VirtualBox, install it:

```bash
vagrant box add solar-project/solar-master
```

To use this box in libvirt you need to convert it using `vagrant-mutate` plugin:

```bash
vagrant plugin install vagrant-mutate
vagrant mutate solar-project/solar-master libvirt
```

You can also change `sync_type` in your custom `vagrant-settings.yaml` file
copied from the `vagrant-settings.yaml_defaults`.

# Use solar

``` bash
vagrant up --provider libvirt
```

(TODO automation required) After that, copy (or create, if missing) the ssh
private keys for nodes to the `.vagrant/machines/solar-dev*/virtualbox` dirs.
And make sure the public keys are listed in the `authorized_keys` files for the
`solar-dev*` nodes.
