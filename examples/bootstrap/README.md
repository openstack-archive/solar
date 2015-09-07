# Demo of the `solar_bootstrap` Resource

You need to instantiate Vagrant with a slave node which is unprovisioned
(i.e. started from the `trusty64` Vagrant box).

You can start the boxes from the Vagrantfile in this directory.

Running
```bash
python example-bootstrap.py deploy
```
will deploy full Solar env to node `solar-dev2`.
