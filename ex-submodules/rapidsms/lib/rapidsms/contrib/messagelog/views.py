#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.template import RequestContext
from django.shortcuts import render_to_response
from rapidsms.models import Contact
from .tables import MessageTable
from .models import Message
from taggit.models import Tag, TaggedItem
import re

def message_log(req, template="messagelog/index.html"):
    messages = Message.objects.all()
    contact = None
    search = None
    show_advanced_filter = None # "Y" to show the advanced filter, "N" to hide it
    all_tags = []               # A distinct list of all tags pertaining to any Messages in the Message Log
    selected_tags = None        # The tags selected by the user by which to filter the Messages
    tag_filter_flag = None      # "Y" if the user chose to do tag filtering, "N" otherwise
    tag_filter_style = None     # Tag filtering style: "any" to show Messages which match any of the selected_tags,
                                #                      "all" to show Messages which match all of the selected tags
    if 'contact' in req.GET:
        if req.GET['contact'] == '':
            contact=None
        else:
            contact = Contact.objects.get(pk=req.GET['contact'])
            messages = messages.filter(contact=contact)

    if 'search' in req.GET and req.GET['search'] != '':
        search = req.GET['search']
        messages = messages.filter(text__iregex=re.escape(search))
    
    # Extract and sort all tag names
    for tag in TaggedItem.tags_for(Message):
        all_tags.append(tag.name)
    all_tags.sort()

    # Retrieve list of selected tags (default to empty list)
    if "selected_tags" in req.GET:
        selected_tags = req.GET.getlist("selected_tags")
    else:
        selected_tags = []

    # Retrieve tag filter flag (default to "N")
    if "tag_filter_flag" in req.GET and req.GET["tag_filter_flag"] == "Y":
        tag_filter_flag = req.GET["tag_filter_flag"]
    else:
        tag_filter_flag = "N"

    # Retrieve advanced filter flag
    if ("show_advanced_filter" in req.GET and req.GET["show_advanced_filter"] == "Y") or (tag_filter_flag == "Y"):
        show_advanced_filter = "Y"
    else:
        show_advanced_filter = "N"

    # Retrieve tag filter style (default to "any")
    if "tag_filter_style" in req.GET and req.GET["tag_filter_style"] == "all":
        tag_filter_style = req.GET["tag_filter_style"]
    else:
        tag_filter_style = "any"

    # If no tags were selected, automatically disable tag filtering
    if len(selected_tags) == 0:
        tag_filter_flag = "N"

    # If the user chose to do tag filtering, perform the filter now
    if tag_filter_flag == "Y":
        if tag_filter_style == "all":
            for tag_name in selected_tags:
                messages = messages.filter(tags__name__in=[tag_name])
        else:
            messages = messages.filter(tags__name__in=selected_tags).distinct()

    return render_to_response(
        template, {
            "messages_table": MessageTable(messages, request=req),
            "search": search,
            "contact": contact,
            "contacts": Contact.objects.all().order_by("name"),
            "show_advanced_filter": show_advanced_filter,
            "all_tags": all_tags,
            "selected_tags": selected_tags,
            "tag_filter_flag": tag_filter_flag,
            "tag_filter_style": tag_filter_style
        }, context_instance=RequestContext(req)
    )
