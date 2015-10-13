Example of using torrent transport with solar. Torrent is used to distribute task data. After fetching is finished torrent client forks and continues seeding.


The example contains single node with single host mapping + transports.

Execute:
```
python examples/torrent/example.py
solar changes stage
solar changes process
solar orch run-once last
```

Wait for finish:

```
solar orch report last -w 100
```

After this you should see new entry in `/etc/hosts` file.


* All created torrents are in `/vagrant/torrents`, it doesn't need to be shared
* Initial seeding is done using torrent file
* Downloading and then seeding is always done with magnetlinks
