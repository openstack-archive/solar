import pytest

from solar.dblayer.solar_models import LogItem


def test_separate_logs():

    history = 'history'
    staged = 'staged'
    history_uids = set()
    staged_uids = set()
    for i in range(2):
        l = LogItem.new({'log': history})
        l.save()
        history_uids.add(l.uid)
    for i in range(3):
        l = LogItem.new({'log': staged})
        l.save()
        staged_uids.add(l.uid)

    assert LogItem.composite.filter({'log': history}) == history_uids
    assert LogItem.composite.filter({'log': staged}) == staged_uids


def test_multiple_filter():

    l1 = LogItem.new({'log': 'history', 'resource': 'a'})
    l2 = LogItem.new({'log': 'history', 'resource': 'b'})

    l1.save()
    l2.save()

    assert LogItem.composite.filter({'log': 'history', 'resource': 'a'}) == {l1.uid}
    assert LogItem.composite.filter({'log': 'history', 'resource': 'b'}) == {l2.uid}


def test_changed_index():

    l = LogItem.new({'log': 'staged', 'resource': 'a', 'action': 'run'})
    l.save()

    assert LogItem.composite.filter({'log': 'staged'}) == {l.uid}
