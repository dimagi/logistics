#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.template import RequestContext
from django.shortcuts import render_to_response
from rapidsms.models import Contact
from .tables import MessageTable
from .models import Message


def message_log(req, template="messagelog/index.html"):
    messages = Message.objects.all()
    contact = None
    search = None
    if 'contact' in req.GET:
        if req.GET['contact'] == '':
            contact=None
        else:
            contact = Contact.objects.get(pk=req.GET['contact'])
            messages = messages.filter(contact=contact)

    if 'search' in req.GET and req.GET['search'] != '':
        search = req.GET['search']
        messages = messages.filter(text__iregex=search)

    return render_to_response(
        template, {
            "messages_table": MessageTable(messages, request=req),
            "search": search,
            "contact": contact,
            "contacts": Contact.objects.all().order_by("name"),
        }, context_instance=RequestContext(req)
    )
