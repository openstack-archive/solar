#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import sys


log = logging.getLogger('solar')


def setup_logger():
    handler = logging.FileHandler('solar.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(funcName)s'
        ' (%(filename)s::%(lineno)s)::%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    print_formatter = logging.Formatter(
        '%(levelname)s (%(filename)s::%(lineno)s)::%(message)s')
    print_handler = logging.StreamHandler(stream=sys.stdout)
    print_handler.setFormatter(print_formatter)
    log.addHandler(print_handler)

    log.setLevel(logging.DEBUG)

setup_logger()
