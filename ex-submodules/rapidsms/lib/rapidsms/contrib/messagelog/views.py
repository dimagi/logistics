#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.template import RequestContext
from django.shortcuts import render_to_response
from rapidsms.models import Contact
from .tables import MessageTable
from .models import Message


def message_log(req, template="messagelog/index.html"):
    contact = None
    if 'contact' in req.GET:
        if req.GET['contact'] == '':
            contact=None
        else:
            contact = Contact.objects.get(pk=req.GET['contact'])

    if contact:
        return render_to_response(
            template, {
                "messages_table": MessageTable(Message.objects.filter(contact=contact), request=req),
                "contact": contact,
                "contacts": Contact.objects.all().order_by("name"),
            }, context_instance=RequestContext(req)
        )
    else:
        return render_to_response(
            template, {
                "messages_table": MessageTable(Message.objects.all(), request=req),
                "contact": None,
                "contacts": Contact.objects.all().order_by("name"),
            }, context_instance=RequestContext(req)
        )
