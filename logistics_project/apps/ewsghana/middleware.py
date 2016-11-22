#
# Copyright (c) 2006-2007, Jared Kuolt
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer in the 
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the SuperJared.com nor the names of its 
#       contributors may be used to endorse or promote products derived from 
#       this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
###

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect

class RequireLoginMiddleware(object):
    """
    Require Login middleware. If enabled, each Django-powered page will
    require authentication.
    
    If an anonymous user requests a page, he/she is redirected to the login
    page set by REQUIRE_LOGIN_PATH or /accounts/login/ by default.
    """
    def __init__(self):
        self.require_login_path = getattr(settings, 'REQUIRE_LOGIN_PATH', '/backdoor/accounts/login/')
    
    def process_request(self, request):
        if request.path != self.require_login_path and \
          settings.MEDIA_URL not in request.path and \
          settings.STATIC_URL not in request.path and \
          request.user.is_anonymous():
            for url in settings.NO_LOGIN_REQUIRED_FOR:
                if url in request.path:
                    return
            if request.POST:
                # hm. is this ok?
                # return login(request)
                return HttpResponseRedirect(self.require_login_path)
            else:
                return HttpResponseRedirect('%s?next=%s' % (self.require_login_path, request.path))

# http://djangosnippets.org/snippets/449/

class AutoLogout:
  def process_request(self, request):
    if not request.user.is_authenticated() :
      return

    try:
      if datetime.now() - request.session['last_touch'] > timedelta( 0, settings.AUTO_LOGOUT_DELAY * 60, 0):
        auth.logout(request)
        del request.session['last_touch']
        return
    except KeyError:
      pass

    request.session['last_touch'] = datetime.now()