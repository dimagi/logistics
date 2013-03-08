#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
import sys
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from rapidsms.conf import settings
from rapidsms.models import Connection, Backend, Contact
from logistics.decorators import place_in_request
from .forms import RegisterUserForm

@transaction.commit_on_success
def my_web_registration(request, Form=RegisterUserForm, 
                        template='web_registration/admin_registration.html', 
                        success_url='admin_web_registration_complete'):
    context = {}
    context['hide_delete'] = True
    return admin_does_all(request, request.user.pk, Form, context, template, success_url)

@transaction.commit_manually
@place_in_request()
def admin_does_all(request, pk=None, Form=RegisterUserForm, context=None, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    context = {} if context is None else context
    user = None
    if pk and not request.user.has_perm('auth.add_user') and \
      not (hasattr(request.user, 'pk') and int(pk) == int(request.user.pk)):
        # view is only available to non-admin users if all they do is edit themselves
        response = HttpResponseRedirect(settings.LOGIN_URL)
        transaction.rollback()
        return response
    if pk is not None:
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            transaction.commit()
            raise Http404
        context['edit_user'] = user
    form = Form(user=user) # An unbound form
    if request.method == 'POST': 
        if request.POST["submit"] == "Delete Contact":
            name = unicode(user)
            user.get_profile().deactivate()
            # here, we choose to completely delete the user
            # and in so doing free up the username for new users to use
            user.delete()
            response = HttpResponseRedirect(
                       "%s?deleted=%s" % (reverse(success_url), name))
            transaction.commit()
            return response
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
                response = render_to_response('web_registration/error.html', 
                                          vals, 
                                          context_instance = RequestContext(request))
                transaction.rollback()
                return response
            else:
                response = HttpResponseRedirect("%s?created=%s" % \
                                            (reverse(success_url), unicode(new_user)))
                transaction.commit()
                return response
    context['users'] = User.objects.all().order_by('username')
    if request.method == 'GET': 
        context['deleted'] = request.GET['deleted'] if "deleted" in request.GET else None
        context['created'] = request.GET['created'] if "created" in request.GET else None
        if 'search' in request.GET:
            search = context['search'] = request.GET['search']
            safe_search = re.escape(search)
            context['users'] = context['users'].filter(Q(username__iregex=safe_search) |\
                                       Q(email__iregex=safe_search) |\
                                       Q(first_name__iregex=safe_search) |\
                                       Q(last_name__iregex=safe_search) |\
                                       Q(logisticsprofile__contact__connection__identity__iregex=safe_search) |\
                                       Q(logisticsprofile__supply_point__name__iregex=safe_search) |\
                                       Q(logisticsprofile__location__name__iregex=safe_search))
    if 'search' not in request.GET and request.location and \
      request.location.code != settings.COUNTRY:
        all_locations = request.location.get_descendants_plus_self()
        context['users'] = context['users'].filter(Q(logisticsprofile__location__in=all_locations)|
                                                   Q(logisticsprofile__supply_point__location__in=\
                                                     all_locations))
    context['form'] = form
    context['location'] = request.location
    if 'destination_url' not in context:
        context['destination_url'] = 'admin_web_registration'
    response = render_to_response(template, context, 
                                  context_instance = RequestContext(request)) 
    transaction.commit()
    return response

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

