#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, settings
from datetime import datetime
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from rapidsms.models import Connection, Backend, Contact
from .forms import AdminRegistersUserForm

@permission_required('auth.add_user')
@transaction.commit_on_success
def admin_does_all(request, pk=None, Form=AdminRegistersUserForm, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    context = {}
    user = None
    if pk is not None:
        user = get_object_or_404(User, pk=pk)
        context['edit_user'] = user
    form = Form(user=user) # An unbound form
    if request.method == 'POST': 
        if request.POST["submit"] == "Delete Contact":
            user.delete()
            return HttpResponseRedirect(
                reverse('admin_web_registration'))
        form = Form(request.POST, user=user) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            try:
                new_user = form.save()
                _send_user_registration_email(new_user.email, 
                                              new_user.username, form.cleaned_data['password1'])
            except:
                vals = {'error_msg':'There was a problem with your request',
                        'error_details':sys.exc_info(),
                        'show_homepage_link': 1 }
                return render_to_response('web_registration/error.html', 
                                          vals, 
                                          context_instance = RequestContext(request))
            else:
                return HttpResponseRedirect( reverse('admin_web_registration'))
    context['form'] = form
    context['users'] = User.objects.all().order_by('username')
    return render_to_response(template, context, 
                              context_instance = RequestContext(request)) 

def _send_user_registration_email(recipient, username, password):
    """ Raises exception on error - returns nothing """
    DNS_name = Site.objects.get(id = settings.SITE_ID).domain
    link = 'http://' + DNS_name + reverse('rapidsms-dashboard')
    
    text_content = """
An administrator of "%s" has set up an account for you.
Your username is "%s", and your password is "%s".
To login, navigate to the following link:
%s
"""
    text_content = text_content % (DNS_name, username, password, link)
    html_content = ''.join(['<p>' + x + '</p>' for x in text_content.strip().split('\n')])
    subject = 'New %s account' % DNS_name
    sender = "no-reply@%s" % DNS_name
    msg = EmailMultiAlternatives(subject, html_content, 
                                 sender, [recipient])
    msg.attach_alternative(html_content, "text/html")
    msg.send()    

