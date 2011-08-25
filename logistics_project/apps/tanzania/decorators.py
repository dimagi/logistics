from django.http import HttpResponseRedirect
from httplib import HTTPSConnection
from django.contrib.sites.models import Site

def gdata_required(f):
    """
    Authenticate against Google GData service
    """
    def wrap(request, *args, **kwargs):
        print "function %s " % f
        if 'token' not in request.GET and 'token' not in request.session:
            # no token at all, request one-time-token
            # next: where to redirect
            # scope: what service you want to get access to
            base_url='https://www.google.com/accounts/AuthSubRequest'
            scope='https://docs.google.com/feeds/%20https://docs.googleusercontent.com/'
            
            urlbase = Site.objects.get_current().domain
            next_url='%s%s' %  (urlbase, request.get_full_path())
            print next_url
            session_val='1'
            target_url="%s?next=%s&scope=%s&session=%s" % (base_url, next_url, scope, session_val)
            return HttpResponseRedirect(target_url)
        elif 'token' not in request.session and 'token' in request.GET:
            # request session token using one-time-token
            print "we got a token"
            conn = HTTPSConnection("www.google.com")
            conn.putrequest('GET', '/accounts/AuthSubSessionToken')
            conn.putheader('Authorization', 'AuthSub token="%s"' % request.GET['token'])
            conn.endheaders()
            conn.send(' ')
            r = conn.getresponse()
            if str(r.status) == '200':
                token = r.read()
                token = token.split('=')[1]
                token = token.replace('', '')
                request.session['token'] = token
        return f(request, *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap

