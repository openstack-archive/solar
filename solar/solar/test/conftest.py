
from pytest import fixture

from solar.interfaces import db


def pytest_configure():
    #db.DB = db.mapping['fakeredis_db']()
    db.DB = db.mapping['neo4j_db']()


@fixture(autouse=True)
def cleanup(request):

    def fin():
        from solar.core import signals

        db.get_db().clear()

    request.addfinalizer(fin)
