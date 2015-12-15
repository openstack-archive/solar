

from solar.orchestration.workers import base


class SubTest(base.Worker):
    """for tests."""

    def pass_two(self, ctxt):
        return 2


def test_subscribe_on_success():
    sub = SubTest()
    test = []
    assert sub.pass_two.on_success(lambda ctxt, rst: test.append(rst)) == None
    assert sub.pass_two({}) == 2
    assert test == [2]


def test_subscribe_for_all():
    sub = SubTest()
    test = []
    sub.for_all.after(lambda ctxt: test.append('after'))
    sub.for_all.before(lambda ctxt: test.append('before'))
    sub.pass_two({})
    assert test == ['before', 'after']
