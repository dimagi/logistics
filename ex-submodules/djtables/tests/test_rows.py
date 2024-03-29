from __future__ import unicode_literals
from builtins import str
from builtins import object
from djtables.table import Table
from djtables.column import Column
from djtables.row import Row


class TestTable(Table):
    name   = Column()
    weapon = Column()


def test_accepts_dicts():
    obj = {
        'name': "Leonardo",
        'weapon': "Katana"
    }

    row = Row(TestTable(), obj)
    assert row.name == obj['name']
    assert row.weapon == obj['weapon']


def test_accepts_objects():
    class MockObject(object):
        def __init__(self, name, weapon):
            self.name = name
            self.weapon = weapon

        def __str__(self):
            return self.name

    obj = MockObject("Michelangelo", "Nunchaku")
    row = Row(TestTable(), obj)

    assert row.name == obj.name
    assert row.weapon == obj.weapon
    assert str(row) == str(obj)


def test_calls_callables():
    obj = {
        'name': lambda: "Donatello",
        'weapon': lambda: "Bo Staff",
    }

    row = Row(TestTable(), obj)
    assert row.name == "Donatello"
    assert row.weapon == "Bo Staff"


def test_returns_none_on_invalid_column():
    row = Row(TestTable(), {})
    assert row.whatever == None


def test_is_iterable():
    data = {
        'name': "Raphael",
        'weapon': "Sai"
    }

    row = Row(TestTable(), data)

    for cell in row:
        assert cell.row == row
        assert cell.value in list(data.values())


def test_has_length():
    row = Row(TestTable(), {})
    assert len(row) == 2
