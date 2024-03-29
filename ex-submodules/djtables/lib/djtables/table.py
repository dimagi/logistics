#!/usr/bin/env python
# vim: et ts=4 sw=4


from __future__ import unicode_literals
from past.builtins import basestring
from builtins import object
from django.template.loader import render_to_string
from .metatable import MetaTable
from .urls import extract, build
from future.utils import with_metaclass


class Table(with_metaclass(MetaTable, object)):
    def __init__(self, object_list=None, request=None, **kwargs):
        self._object_list = object_list
        self._request = request
        self._paginator = None
        self.new_columns = []

        if request is not None:
            prefix = kwargs.get('prefix', "")
            kwargs.update(extract(request.GET, prefix))

        if len(kwargs):
            self._meta = self._meta.fork(
                **kwargs )

    def get_url(self, **kwargs):
        """
        Return an url, relative to the request associated with this
        table. Any keywords arguments provided added to the query
        string, replacing existing values.
        """

        return build(
            self._request.path,
            self._request.GET,
            self._meta.prefix,
            **kwargs )

    @property
    def object_list(self):
        """
        Return this table's object_list, transformed (sorted, reversed,
        filtered, etc) according to its meta options.
        """

        def _sort(ob, ol):
            reverse = ob.startswith("-")
            ob = ob[1:] if reverse else ob
            for column in self.columns:
                if column.sort_key_fn is not None and column.name == ob:
                    return sorted(ol, key=column.sort_key_fn, reverse=reverse)
            if self._meta.order_by and hasattr(ol, "order_by"):
                return ol.order_by(*self._meta.order_by.split("|"))
            return ol

        ol = self._object_list
        ob = self._meta.order_by
        if not ob: return ol
        if isinstance(ob, basestring):
            return _sort(ob, ol)
        elif isinstance(ob, list):
            ob.reverse()
            for fn in ob:
                ol = _sort(fn, ol)
        return ol

    def as_html(self): # pragma: no cover
        """
        Return this table as HTML, ready to be inserted into a template.
        To customize the output, set the ``template`` meta option to a
        new template, and use the table_tags to build your own template.
        See README for examples.
        """

        return render_to_string(
            self._meta.template,
            { "table": self } )

    @property
    def paginator(self):
        if self._paginator is None:
            self._paginator = self._meta.paginator_class(
                self.object_list, self._meta.per_page )

        return self._paginator

    @property
    def columns(self):
        """Return the list of columns."""
        return self._meta.columns + self.new_columns

    def add_column(self, column, name):
        self.new_columns.append(column)
        column.bind_to(self, name)

    @property
    def rows(self):
        """Return the list of object on the active page."""

        return [self._meta.row_class(self, o) for o in self.paginator.page(self._meta.page).object_list]

    def cell(self, column, row):
        return self._meta.cell_class(
            column, row )
