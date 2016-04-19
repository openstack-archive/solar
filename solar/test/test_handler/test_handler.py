#    Copyright 2016 Mirantis, Inc.
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

import pytest

from solar.core.handlers.base import BaseHandler
from solar.core.transports.base import SolarTransportResult
from solar.errors import SolarError


def test_verify_run_raises_stdout_and_stderr():
    handler = BaseHandler(None)

    result = SolarTransportResult()
    result.stdout = 'stdout'
    result.stderr = 'stderr'
    result.return_code = 1

    with pytest.raises(SolarError) as excinfo:
        handler.verify_run_result('', result)
    assert result.stdout in excinfo.value.message
    assert result.stderr in excinfo.value.message
