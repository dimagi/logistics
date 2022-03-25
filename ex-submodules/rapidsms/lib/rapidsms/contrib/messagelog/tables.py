#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from builtins import object
from django.conf import settings
from djtables import Table, Column
from djtables.column import DateColumn
from .models import Message


class MessageTable(Table):

    # this is temporary, until i fix ModelTable!
    contact = Column(sortable=False)
    connection = Column(sortable=False)
    direction = Column(sortable=False)
    date = DateColumn(format="H:i d/m/Y")
    text = Column(css_class="message", sortable=False)
    tags = Column(sortable = False, value = lambda cell: cell.object.get_tags_for_display())

    class Meta(object):
        #model = Message
        #exclude = ['id']
        order_by = '-date'
