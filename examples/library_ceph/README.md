Current example will do following things:

- fetch fuel-library from github
- use ./update_modules.sh to fetch librarian dependencies
- generate ceph keys on a solar-dev1
- install ceph-mon on solar-dev1 (INPROGRESS)
- install ceph-osd on solar-dev2 (TODO)
- imlement removal mechanism for ceph-mon/ceph-osd (TODO)


To use it:

```
python exaples/library_ceph/ceph.py
solar ch stage && solar ch process
solar or run-once last -w 120
```

If it will fail you can run particular resource action, with a lot of
debug info.

```
solar res action run ceph_mon1
```

To add repositories use

```
solar resource create apt1 templates/mos_repos node=node1 index=1
```
