.. Solar documentation master file, created by
   sphinx-quickstart on Thu Nov 26 12:41:37 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Solar's documentation!
=================================

Solar provides flexible orchestration and resource management framework for
deploying distributed systems. It leverages abstraction layer over commonly
used configuration management systems like puppet, ansible etc. to enable
complex, multi node orchestration.

Solar can be used as separate tool for quick prototyping deployment topology,
but as a framework it can be also integrated with existing tools used to
configure and deploy distributed systems including
OpenStack clouds. Solar also provides control over resulting changes by
introducing changes log and history for deployment entities. This enables more
control over lifecycle management of infrastructure.

Solar can deploy and manage any distributed system, focusing on OpenStack
ecosystem e.g. OpenStack itself, Ceph, etc. There are also other examples
like Riak.

Contents:

.. toctree::
   :maxdepth: 2

   installation
   usage
   tutorials/index
   development
   glossary
   architecture
   resource
   resource_repository
   orchestration/index
   transports
   examples
   deployment_plan
   faq


Indices and tables
==================

* :ref:`search`

