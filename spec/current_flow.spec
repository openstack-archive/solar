

1. Discovery (ansible all -m facter)
Read list of ips and store them, and search for different data on those
hosts

2. Create environment ?? with profile, that provides roles (wraps resources)

3. Add nodes to the env and distribute services

Assign roles (partitions of services) from the profiles to the nodes.
Store history of applied resources.
Role only matters as initial template.

4. Change settings provided by resource.

Imporant/Non important settings ??
We need defaults for some settings.
Different templates ?? for different backends of resources ??

5. Start management

Periodicly applying stuff ??

6. Stop management

We need to be able to stop things

7. Run maintenance

Resources should added to history and management graph will be changed

8. Start management
