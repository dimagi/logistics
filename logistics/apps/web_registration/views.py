#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys
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
from django.utils import simplejson
from rapidsms.conf import settings
from rapidsms.contrib.locations.models import Location
from .forms import AdminRegistersUserForm

@transaction.commit_on_success
def my_web_registration(request, Form=AdminRegistersUserForm, 
                        template='web_registration/admin_registration.html', 
                        success_url='admin_web_registration_complete'):
    context = {}
    context['hide_delete'] = True
    return admin_does_all(request, request.user.pk, Form, context, template, success_url)

@transaction.commit_on_success
def admin_does_all(request, pk=None, Form=AdminRegistersUserForm, context={}, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    if not request.user.has_perm('auth.add_user') and pk != request.user.pk:
        # view is only available to non-admin users if all they do is edit themselves
        return HttpResponseRedirect(settings.LOGIN_URL)
    user = None
    if pk is not None:
        user = get_object_or_404(User, pk=pk)
        context['edit_user'] = user
    form = Form(user=user) # An unbound form
    if request.method == 'POST': 
        if request.POST["submit"] == "Delete Contact":
            user.delete()
            return HttpResponseRedirect(
                reverse(success_url))
        form = Form(request.POST, user=user) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            try:
                new_user = form.save()
                if user is None:
                    # only send this if the account was created brand-new
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
                return HttpResponseRedirect( reverse(success_url))
    context['form'] = form
    context['users'] = User.objects.all().order_by('username')
    context.update(get_nav_context())
    return render_to_response(template, context, 
                              context_instance = RequestContext(request)) 
    
def get_nav_context():
    context = {}
    country = Location.objects.get(code=settings.COUNTRY)
    regions_qs = country.get_children().order_by('name')
    context['regions'] = regions_qs #simplejson.dumps([r.name for r in regions_qs])

    districts = {}
    districts_qs = Location.objects.none()
    for r in regions_qs:
        # TODO: optimize this to use mptt
        qs = r.get_children()
        districts[r.name] = [c.name for c in qs.order_by('name')]
        districts_qs = districts_qs | qs
    context['districts'] = simplejson.dumps(districts)
    
    facilities = {}
    for d in districts_qs:
        facilities[d.name] = [f.name for f in d.all_facilities().order_by('name')]
    context['facilities'] = simplejson.dumps(facilities)
    return context

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

