
from pytest import fixture

from solar.interfaces import db


def pytest_configure():
    if db.CURRENT_DB == 'redis_graph_db':
        db.DB = db.mapping['fakeredis_graph_db']()
    elif db.CURRENT_DB == 'redis_db':
        db.DB = db.mapping['fakeredis_db']()
    else:
        db.DB = db.mapping[db.CURRENT_DB]()


@fixture(autouse=True)
def cleanup(request):

    def fin():
        from solar.core import signals

        db.get_db().clear()

    request.addfinalizer(fin)
