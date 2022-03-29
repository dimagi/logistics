#!/usr/bin/env python
# vim: et ts=4 sw=4


from __future__ import unicode_literals
from builtins import str
from builtins import object
class Row(object):
    def __init__(self, table, obj):
        self.table = table
        self.obj = obj

    def __getattr__(self, name):
        if hasattr(self.obj, name):
            val = getattr(self.obj, name)

        elif hasattr(self.obj, "__getitem__") and (name in self.obj):
            val = self.obj[name]

        else:
            val = None

        return callable(val) and val() or val

    def __str__(self):
        return str(self.obj)

    def __iter__(self):
        for column in self.table.columns:
            yield self.table.cell(column, self)

    def __len__(self):
        return len(self.table.columns)
