
import random
import string

import pytest
import mock


@pytest.fixture
def address():
    return 'ipc:///tmp/solar_test_' + ''.join(
        (random.choice(string.ascii_lowercase) for x in xrange(4)))


@pytest.fixture
def tracer(request):
    return mock.Mock()

