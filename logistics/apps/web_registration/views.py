#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, settings
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from rapidsms.models import Connection, Backend, Contact
from .forms import AdminRegistersUserForm

@transaction.commit_manually
def admin_does_all(request, template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    if request.method == 'POST': # If the form has been submitted...
        form = AdminRegistersUserForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            try:
                new_user = User()
                new_user.username = form.cleaned_data['username']
                new_user.email = form.cleaned_data['email']
                new_user.set_password(form.cleaned_data['password1'])
                
                new_user.is_staff = False # Can never log into admin site
                new_user.is_active = form.cleaned_data['is_active']
                new_user.is_superuser = form.cleaned_data['is_admin']   
                new_user.last_login =  datetime(1970,1,1)
                # date_joined is used to determine expiration of the invitation key - I'd like to
                # munge it back to 1970, but can't because it makes all keys look expired.
                new_user.date_joined = datetime.utcnow()
                new_user.save()
                if 'location' in form.cleaned_data or 'facility' in form.cleaned_data:
                    profile = new_user.get_profile()
                    profile.location = form.cleaned_data['location']
                    profile.facility = form.cleaned_data['facility']
                    profile.save()
                    
                _send_user_registration_email(new_user.email, 
                                              new_user.username, form.cleaned_data['password1'])
            except:
                transaction.rollback()                
                vals = {'error_msg':'There was a problem with your request',
                        'error_details':sys.exc_info(),
                        'show_homepage_link': 1 }
                return render_to_response('web_registration/error.html', 
                                          vals, 
                                          context_instance = RequestContext(request))
            else:
                transaction.commit()  
                return HttpResponseRedirect( reverse(success_url, 
                                                     kwargs={'caller':'admin', 
                                                             'account':new_user.username}) )
    else:
        form = AdminRegistersUserForm() # An unbound form
   
    return render_to_response(template, 
                              {'form': form, 
                               'users': User.objects.all().order_by('username')}, 
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

