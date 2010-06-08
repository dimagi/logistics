#!/usr/bin/env python
# vim: et ts=4 sw=4


class Column(object):

    """
    This class represents a table column. It is responsible for holding
    metadata, and rending table cells. Like Django's model fields, table
    cells are usually created within the class which they are bound to.
    """

    creation_counter = 0

    def __init__(self, name=None, sortable=True):
        self._name = name
        self.sortable = sortable

        # like django fields, keep track of the order which columns are
        # created, so they can be sorted later. (unfortunately, python
        # attrs are passed to __new__ as an unsorted dict, so we must
        # keep track of this manually to avoid random column order.)
        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

        self.bound_to = None

    def __lt__(self, other):
        """Allow columns to be sorted by order of creation."""
        return self.creation_counter < other.creation_counter

    def __unicode__(self):
        return self.name

    def bind_to(self, table, name):
        """
        Bind this column to a table, and assign it a name. This method
        can only be called once per instance, because a Column cannot be
        bound to multiple tables. (The sort order would be ambiguous.)
        """

        if self.bound_to is not None:
            raise AttributeError(
                "Column is already bound to '%s' as '%s'" %\
                    self.bound_to)

        self.bound_to = (table, name)

    @property
    def is_bound(self):
        """Return true if this column is bound to a table."""
        return (self.bound_to is not None)

    @property
    def name(self):
        """Return the column name, whether explicit or implicit."""
        return self._name or self.bound_to[1]

    def render(self, value):
        """
        Return ``value`` ready for display. The default behavior is to
        simply cast it to unicode, but this may be overridden by child
        classes to do something more useful.
        """
        return unicode(value)


class BoundColumn(object):

    """
    This class wraps a Column instance, and binds it to a Table instance
    to provide useful properties to the template. This represents a per-
    render instance of the column, containing its volatile state, such
    as sort order. (More properties, such as visibility, filtering, and
    grouping may come later.)

    All of the attributes (and methods) of the wrapped Column can be
    accessed via this class, with help from some __getattr__ magic.
    """

    def __init__(self, table, column):
        self.table = table
        self.column = column

    def sort_url(self):
        return self.table.get_url(order_by=self.column.name)

    def is_sorted(self):
        return self.table._meta.order_by == self.column.name

    def sort_direction(self):
        return "asc"

    def __unicode__(self):
        return unicode(self.column)

    def __getattr__(self, name):
        return getattr(self.column, name)
