#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License attached#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

import struct

REPLY_OK = 2
REPLY_GEN_OK = 20
REPLY_GEN_END = 21
REPLY_FAIL = 0
REPLY_ERR = 1


HDR = "<I"
HDR_SIZE = struct.calcsize(HDR)

INT_DEFAULT_REPLY_TYPE = 0
INT_GENERATOR_REPLY_TYPE = 1
