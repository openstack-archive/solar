#!/bin/sh
# fix 'module' object has no attribute 'add_metaclass'
pip uninstall -y six
pip install six
